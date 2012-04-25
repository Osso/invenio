# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

__revision__ = "$Id$"

import re
import time
import sys
import os
import zlib
from itertools import islice

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from invenio.dbquery import run_sql, serialize_via_marshal, \
                            deserialize_via_marshal
from invenio.search_engine import search_pattern, search_unit
from invenio.search_engine_utils import get_fieldvalues
from invenio.bibformat_utils import parse_tag
from invenio.bibknowledge import get_kb_mappings
from invenio.bibtask import write_message, task_get_option, \
                     task_update_progress, task_sleep_now_if_required, \
                     task_get_task_param
from invenio.errorlib import register_exception
from invenio.intbitset import intbitset


class memoise:
    def __init__(self, function):
        self.memo = {}
        self.function = function

    def __call__(self, *args):
        if args not in self.memo:
            self.memo[args] = self.function(*args)
        return self.memo[args]

INTBITSET_OF_DELETED_RECORDS = search_unit(p='DELETED', f='980', m='a')


#@memoise
def get_recids_matching_query(pvalue, fvalue, m='e'):
    """Return set of recIDs matching query for PVALUE and FVALUE."""
    return search_pattern(p=pvalue, f=fvalue, m=m) - INTBITSET_OF_DELETED_RECORDS


def get_citation_weight(rank_method_code, config, chunk_size=5000):
    """return a dictionary which is used by bibrank daemon for generating
    the index of sorted research results by citation information
    """
    begin_time = time.time()
    last_update_time = get_bibrankmethod_lastupdate(rank_method_code)

    if task_get_option("quick") == "no":
        last_update_time = "0000-00-00 00:00:00"
        write_message("running thorough indexing since quick option not used",
                      verbose=3)

    try:
        # check indexing times of `journal' and `reportnumber`
        # indexes, and only fetch records which have been indexed
        sql = "SELECT DATE_FORMAT(MIN(last_updated), " \
              "'%%Y-%%m-%%d %%H:%%i:%%s') FROM idxINDEX WHERE name IN (%s,%s)"
        index_update_time = run_sql(sql, ('journal', 'reportnumber'), 1)[0][0]
    except IndexError:
        write_message("Not running citation indexer since journal/reportnumber"
                      " indexes are not created yet.")
        index_update_time = "0000-00-00 00:00:00"

    last_modified_records = get_last_modified_rec(last_update_time,
                                                  index_update_time)
    # id option forces re-indexing a certain range
    # even if there are no new recs
    if last_modified_records or task_get_option("id"):
        if task_get_option("id"):
            # construct a range of records to index
            taskid = task_get_option("id")
            first = taskid[0][0]
            last = taskid[0][1]
            # Make range, last+1 so that
            # e.g. -i 1-2 really means [1,2] not [1]
            updated_recid_list = range(first, last+1)
        else:
            updated_recid_list = create_recordid_list(last_modified_records)

        write_message("Last update %s records: %s updates: %s" % \
                                                (last_update_time,
                                                 len(last_modified_records),
                                                 len(updated_recid_list)))

        # result_intermediate should be warranted to exists!
        # but if the user entered a "-R" (do all) option, we need to
        # make an empty start set
        quick = task_get_option("quick") != "no"
        if quick:
            cites_weight = last_updated_result(rank_method_code)
            cites = get_cit_dict("citationdict")
            refs = get_cit_dict("reversedict")
            selfcites = get_cit_dict("selfcitdict")
            selfrefs = get_cit_dict("selfcitedbydict")
            authorcites = get_initial_author_dict()
        else:
            cites_weight, cites, refs = {}, {}, {}
            selfcites, selfrefs, authorcites = {}, {}, {}

        # Enrich updated_recid_list so that it would contain also
        # records citing or referring to updated records, so that
        # their citation information would be updated too.  Not the
        # most efficient way to treat this problem, but the one that
        # requires least code changes until ref_analyzer() is more
        # nicely re-factored.
        updated_recid_list_set = intbitset(updated_recid_list)
        for somerecid in updated_recid_list:
            # add both citers and citees:
            updated_recid_list_set |= intbitset(cites.get(somerecid, []))
            updated_recid_list_set |= intbitset(refs.get(somerecid, []))

        # Split records to process into chunks so that we do not
        # fill up too much memory
        updated_recid_iter = iter(updated_recid_list_set)

        while True:
            task_sleep_now_if_required()
            chunk = list(islice(updated_recid_iter, chunk_size))
            if not chunk:
                break
            write_message("Processing chunk #%s to #%s" % (chunk[0], chunk[-1]))
            cites_weight, cites, refs, selfcites, selfrefs, authorcites \
                        = process_chunk(chunk,
                                        config,
                                        cites_weight,
                                        cites,
                                        refs,
                                        selfcites,
                                        selfrefs,
                                        authorcites)

            if quick:
                # Store partial result as it is just an update and not
                # a creation from scratch
                insert_cit_ref_list_intodb(cites,
                                           refs,
                                           selfcites,
                                           selfrefs,
                                           authorcites)

        end_time = time.time()
        write_message("Total time of get_citation_weight(): %.2f sec" % \
                                                      (end_time - begin_time))
        task_update_progress("citation analysis done")
    else:
        cites_weight = {}
        write_message("No new records added since last time this " \
                      "rank method was executed")

    return cites_weight, index_update_time


def process_chunk(recids, config, cites_weight, cites,
                                refs, selfcites, selfrefs, authorcites):
    # call the procedure that does the hard work by reading fields of
    # citations and references in the updated_recid's (but nothing else)!
    write_message("Entering get_citation_informations", verbose=9)
    citation_informations = get_citation_informations(recids, config)
    # write_message("citation_informations: "+str(citation_informations))
    # create_analysis_tables() #temporary..
                              #test how much faster in-mem indexing is
    write_message("Entering ref_analyzer", verbose=9)
    # call the analyser that uses the citation_informations to really
    # search x-cites-y in the coll..
    return ref_analyzer(citation_informations,
                       cites_weight,
                       cites,
                       refs,
                       selfcites,
                       selfrefs,
                       authorcites,
                       config,
                       recids)
    # dic is docid-numberofreferences like {1: 2, 2: 0, 3: 1}
    # write_message("Docid-number of known references "+str(dic))


def get_bibrankmethod_lastupdate(rank_method_code):
    """return the last excution date of bibrank method
    """
    query = "SELECT last_updated FROM rnkMETHOD WHERE name = %s"
    last_update_time = run_sql(query, [rank_method_code])
    try:
        r = last_update_time[0][0]
    except IndexError:
        r = None

    if r is None:
        r = "0000-00-00 00:00:00"

    return r


def get_last_modified_rec(bibrank_method_lastupdate, indexes_lastupdate):
    """Get records to be updated by bibrank indexing

    Return the list of records which have been modified between the last
    execution of bibrank method and the latest journal/report index updates.
    The result is expected to have ascending id order.
    """
    query = """SELECT id FROM bibrec
               WHERE modification_date >= %s
               AND modification_date < %s
               ORDER BY id ASC"""
    return run_sql(query, (bibrank_method_lastupdate, indexes_lastupdate))


def create_recordid_list(rec_ids):
    """Create a list of record ids out of RECIDS.
       The result is expected to have ascending numerical order.
    """
    return [row[0] for row in rec_ids]


def last_updated_result(rank_method_code):
    """ return the last value of dictionary in rnkMETHODDATA table if it
        exists and initialize the value of last updated records by zero,
        otherwise an initial dictionary with zero as value for all recids
    """
    query = """SELECT relevance_data FROM rnkMETHOD, rnkMETHODDATA WHERE
               rnkMETHOD.id = rnkMETHODDATA.id_rnkMETHOD
               AND rnkMETHOD.Name = '%s'""" % rank_method_code
    try:
        rdict = run_sql(query)[0][0]
    except IndexError:
        rdict = None

    dic = {}
    if rdict:
        # has to be prepared for corrupted data!
        try:
            dic = deserialize_via_marshal(rdict)
        except zlib.error:
            pass
    return dic


def format_journal(format_string, mappings):
    """format the publ infostring according to the format"""

    def replace(char, data):
        return data.get(char, char)

    return ''.join(replace(c, mappings) for c in format_string)


def get_citation_informations(recid_list, config):
    """scans the collections searching references (999C5x -fields) and
       citations for items in the recid_list
       returns a 4 list of dictionaries that contains the citation information
       of cds records
       examples: [ {} {} {} {} ]
                 [ {5: 'SUT-DP-92-70-5'},
                   { 93: ['astro-ph/9812088']},
                   { 93: ['Phys. Rev. Lett. 96 (2006) 081301'] }, {} ]
        NB: stuff here is for analysing new or changed records.
        see "ref_analyzer" for more.
    """
    begin_time = os.times()[4]
    d_reports_numbers = {}  # dict of recid -> institute-given-report-code
    d_references_report_numbers = {}  # dict of recid -> ['astro-ph/xyz']
    d_references_s = {}  # dict of recid -> list_of_the_entries_of_this_recs_bibliography
    d_records_s = {}  # dict of recid -> this_records_publication_info

    function = config.get("rank_method", "function")
    write_message("config function %s" % function, verbose=9)
    record_pri_number_tag = config.get(function, "primary_report_number")
    record_add_number_tag = config.get(function, "additional_report_number")
    reference_number_tag = config.get(function, "reference_via_report_number")
    reference_tag = config.get(function, "reference_via_pubinfo")

    p_record_pri_number_tag = tagify(parse_tag(record_pri_number_tag))
    # 037a: contains (often) the "hep-ph/0501084" tag of THIS record
    p_record_add_number_tag = tagify(parse_tag(record_add_number_tag))
    # 088a: additional short identifier for the record
    p_reference_number_tag = tagify(parse_tag(reference_number_tag))
    # 999C5r. this is in the reference list, refers to other records. Looks like: hep-ph/0408002
    p_reference_tag = tagify(parse_tag(reference_tag))
    # 999C5s. A standardized way of writing a reference in the reference list. Like: Nucl. Phys. B 710 (2000) 371
    #fields needed to construct the pubinfo for this record
    publication_pages_tag = ""
    publication_year_tag = ""
    publication_journal_tag = ""
    publication_volume_tag = ""
    publication_format_string = "p v (y) c"

    tag = config.get(function, "pubinfo_journal_page")
    publication_pages_tag = tagify(parse_tag(tag))
    tag = config.get(function, "pubinfo_journal_year")
    publication_year_tag = tagify(parse_tag(tag))
    tag = config.get(function, "pubinfo_journal_title")
    publication_journal_tag = tagify(parse_tag(tag))
    tag = config.get(function, "pubinfo_journal_volume")
    publication_volume_tag = tagify(parse_tag(tag))
    publication_format_string = config.get(function, "pubinfo_journal_format")

    #print values for tags for debugging
    if task_get_task_param('verbose') >= 9:
        write_message("tag values")
        write_message("p_record_pri_number_tag %s" % p_record_pri_number_tag)
        write_message("p_reference_tag %s" % p_reference_tag)
        write_message("publication_journal_tag %s" % publication_journal_tag)
        write_message("publication_format_string is %s" % publication_format_string)

    # perform quick check to see if there are some records with
    # reference tags, because otherwise get.cit.inf would be slow even
    # if there is nothing to index:
    if run_sql("SELECT value FROM bib%sx WHERE tag=%%s LIMIT 1" % p_reference_tag[0:2],
               (p_reference_tag,)) or \
       run_sql("SELECT value FROM bib%sx WHERE tag=%%s LIMIT 1" % p_reference_number_tag[0:2],
               (p_reference_number_tag,)):

        done = 0  # for status reporting
        for recid in recid_list:
            if done % 10 == 0:
                task_sleep_now_if_required()
                # in fact we can sleep any time here

            if done % 1000 == 0:
                mesg = "get cit.inf done %s of %s" % (done, len(recid_list))
                write_message(mesg)
                task_update_progress(mesg)

            done += 1

            if recid in INTBITSET_OF_DELETED_RECORDS:
                # do not treat this record since it was deleted; we
                # skip it like this in case it was only soft-deleted
                # e.g. via bibedit (i.e. when collection tag 980 is
                # DELETED but other tags like report number or journal
                # publication info remained the same, so the calls to
                # get_fieldvalues() below would return old values)
                continue

            pri_report_numbers = get_fieldvalues(recid,
                                                 p_record_pri_number_tag)
            add_report_numbers = get_fieldvalues(recid,
                                                 p_record_add_number_tag)
            reference_report_numbers = get_fieldvalues(recid,
                                                       p_reference_number_tag)
            references_s = get_fieldvalues(recid, p_reference_tag)

            l_report_numbers = pri_report_numbers
            l_report_numbers.extend(add_report_numbers)
            d_reports_numbers[recid] = l_report_numbers

            if reference_report_numbers:
                d_references_report_numbers[recid] = reference_report_numbers

            references_s = get_fieldvalues(recid, p_reference_tag)
            msg = "%s's %s values %s" % (recid, p_reference_tag, references_s)
            write_message(msg, verbose=9)
            if references_s:
                d_references_s[recid] = references_s

            # get a combination of
            # journal vol (year) pages
            if publication_pages_tag and publication_journal_tag and \
                 publication_volume_tag and publication_year_tag and \
                 publication_format_string:
                tagsvalues = {}  # we store the tags and their values here
                                 # like c->444 y->1999 p->"journal of foo",
                                 # v->20
                tmp = get_fieldvalues(recid, publication_journal_tag)
                if tmp:
                    tagsvalues["p"] = tmp[0]
                tmp = get_fieldvalues(recid, publication_volume_tag)
                if tmp:
                    tagsvalues["v"] = tmp[0]
                tmp = get_fieldvalues(recid, publication_year_tag)
                if tmp:
                    tagsvalues["y"] = tmp[0]
                tmp = get_fieldvalues(recid, publication_pages_tag)
                if tmp:
                    # if the page numbers have "x-y" take just x
                    pages = tmp[0]
                    hpos = pages.find("-")
                    if hpos > 0:
                        pages = pages[:hpos]
                    tagsvalues["c"] = pages

                # check if we have the required data
                ok = True
                for c in publication_format_string:
                    if c in ('p', 'v', 'y', 'c'):
                        if c not in tagsvalues:
                            ok = False

                if ok:
                    publ = format_journal(publication_format_string,
                                          tagsvalues)
                    d_records_s[recid] = [publ]

                    # Add codens
                    for coden in get_kb_mappings('CODENS',
                                                 value=tagsvalues['p']):
                        tagsvalues['p'] = coden['key']
                        c = format_journal(publication_format_string,
                                           tagsvalues)
                        d_records_s[recid].append(c)

                    write_message("d_records_s (publication info) for " \
                                  "%s is %s" % (recid, d_records_s[recid]),
                                  verbose=9)

    else:
        mesg = "Warning: there are no records with tag values for " \
               "%s or %s. Nothing to do." % \
                                    (p_reference_number_tag, p_reference_tag)
        write_message(mesg)

    mesg = "get cit.inf done fully"
    write_message(mesg)
    task_update_progress(mesg)

    end_time = os.times()[4]
    write_message("Execution time for generating citation info "
                  "from record: %.2f sec" % (end_time - begin_time))
    return d_reports_numbers, d_references_report_numbers, \
           d_references_s, d_records_s,


def prepare_self_citations_cache(updated_records_list, references_dict):
    from invenio.bibrank_selfcites_task import compute_and_store_self_citations
    from invenio.bibrank_selfcites_indexer import get_authors_tags, \
                                                  fetch_references

    tags = get_authors_tags()

    to_update = set()
    for recid in updated_records_list:
        to_update.add(recid)
        # References that were in the self-citations dict but
        # were deleted, we need to reprocesss these records
        to_update.update(fetch_references(recid))
        # References that are new
        to_update.update(references_dict.get(recid, set()))

    for index, recid in enumerate(to_update):
        if index % 10 == 0:
            task_sleep_now_if_required()

        if index % 1000 == 0:
            mesg = "Self cite done %d of %d" % (index, len(to_update))
            write_message(mesg)
            task_update_progress(mesg)

        compute_and_store_self_citations(recid, tags)


def get_self_citations(updated_records_list, citations_dict, references_dict,
                       initial_selfcites, initial_selfrefs, config):
    """Check which items have been cited by one of the authors of the
       citing item: go through id's in new_record_list, use citationdic
       to get citations, update "selfcites". Selfcites is originally
       initial_selfcitdict. Return selfcites.
    """
    from invenio.bibrank_selfcites_indexer import compute_self_citations, \
                                                  get_authors_tags
    tags = get_authors_tags()
    selfcites = initial_selfcites
    selfcitedbydic = initial_selfrefs

    to_update = set()
    for recid in updated_records_list:
        to_update.add(recid)
        # References that are in the self-citations dict but
        # were deleted, we need to reprocesss these records
        to_update.update(selfcitedbydic.get(recid, set()))
        # References that are new
        to_update.update(references_dict.get(recid, set()))

    for index, recid in enumerate(to_update):
        if index % 10 == 0:
            task_sleep_now_if_required()

        if index % 1000 == 0:
            mesg = "Self cite done %d of %d" % (index, len(to_update))
            write_message(mesg)
            task_update_progress(mesg)

        self_citations = compute_self_citations(recid, tags)
        if self_citations:
            selfcites[recid] = self_citations
        else:
            try:
                del selfcites[recid]
            except KeyError:
                pass

    mesg = "Selfcites done fully"
    write_message(mesg)
    task_update_progress(mesg)

    return selfcites


def get_author_citations(updated_redic_list, citedbydict,
                         initial_author_dict, config):
    """Traverses citedbydict in order to build "which author is quoted where" dict.
       The keys of this are author names. An entry like "Apollinaire"->[1,2,3] means
       Apollinaire is cited in records 1,2 and 3.
       Input: citedbydict, updated_redic_list = records to be searched, initial_author_dict:
              the dicts from the database.
       Output: authorciteddict. It is initially set to initial_author_dict
    """

    #sorry bout repeated code to get the tags
    tags = ['first_author', 'additional_author', 'alternative_author_name']
    tagvals = {}
    for t in tags:
        try:
            x = config.get(config.get("rank_method", "function"), t)
            tagvals[t] = x
        except:
            register_exception(prefix="attribute "+t+" missing in config", alert_admin=True)
            return initial_author_dict

    # Parse the tags
    mainauthortag = tagify(parse_tag(tagvals['first_author']))
    coauthortag = tagify(parse_tag(tagvals['additional_author']))
    extauthortag = tagify(parse_tag(tagvals['alternative_author_name']))
    if task_get_task_param('verbose') >= 9:
        write_message("mainauthortag "+mainauthortag)
        write_message("coauthortag "+coauthortag)
        write_message("extauthortag "+extauthortag)

    author_cited_in = initial_author_dict
    if citedbydict:
        i = 0  # just a counter for debug
        write_message("Checking records referred to in new records")
        for u in updated_redic_list:
            if i % 10 == 0:
                task_sleep_now_if_required()

            if i % 1000 == 0:
                mesg = "Author ref done %s of %s records" % (i, len(updated_redic_list))
                write_message(mesg)
                task_update_progress(mesg)
            i = i + 1

            if u in citedbydict:
                these_cite_k = citedbydict[u]
                if these_cite_k is None:
                    these_cite_k = []  # verify it is an empty list, not None
                authors = get_fieldvalues(u, mainauthortag)
                coauthl = get_fieldvalues(u, coauthortag)
                extauthl = get_fieldvalues(u, extauthortag)
                authors.extend(coauthl)
                authors.extend(extauthl)
                for a in authors:
                    if a and a in author_cited_in:
                        # add all elements in these_cite_k
                        # that are not there already
                        for citer in these_cite_k:
                            tmplist = author_cited_in[a]
                            if (tmplist.count(citer) == 0):
                                tmplist.append(citer)
                                author_cited_in[a] = tmplist
                            else:
                                author_cited_in[a] = these_cite_k

        mesg = "Author ref done fully"
        write_message(mesg)
        task_update_progress(mesg)

        # Go through the dictionary again: all keys but search only
        # if new records are cited
        write_message("Checking authors in new records")
        i = 0
        for k in citedbydict.keys():
            if i % 1000 == 0:
                mesg = "Author cit done %s of %s records" % (i, len(citedbydict.keys()))
                write_message(mesg)
                task_update_progress(mesg)
            i += i

            these_cite_k = citedbydict[k]
            if these_cite_k is None:
                these_cite_k = []  # verify it is an empty list, not None
            # do things only if these_cite_k contains any new stuff
            intersec_list = list(set(these_cite_k) & set(updated_redic_list))
            if intersec_list:
                authors = get_fieldvalues(k, mainauthortag)
                coauthl = get_fieldvalues(k, coauthortag)
                extauthl = get_fieldvalues(k, extauthortag)
                authors.extend(coauthl)
                authors.extend(extauthl)
                for a in authors:
                    if a and a in author_cited_in:
                        # add all elements in these_cite_k
                        # that are not there already
                        for citer in these_cite_k:
                            tmplist = author_cited_in[a]
                            if (tmplist.count(citer) == 0):
                                tmplist.append(citer)
                                author_cited_in[a] = tmplist
                            else:
                                author_cited_in[a] = these_cite_k

        mesg = "Author cit done fully"
        write_message(mesg)
        task_update_progress(mesg)

    return author_cited_in


def standardize_report_number(report_number):
    # Remove category for arxiv papers
    return re.sub(ur'(arXiv:\d{4}\.\d{4}) \[[a-z-]+\]',
                  ur'\g<1>',
                  report_number,
                  re.I | re.U)


def ref_analyzer(citation_informations, citations_weight, citations,
                 references, selfcites, selfrefs, authorcites,
                 config, updated_recids):
    """Analyze the citation informations and calculate the citation weight
       and cited by list dictionary.
    """
    function = config.get("rank_method", "function")
    pubrefntag = config.get(function, "reference_via_report_number")
    pubreftag = config.get(function, "reference_via_pubinfo")

    # pubrefntag is often 999C5r, pubreftag 999C5s
    write_message("pubrefntag %s" % pubrefntag, verbose=9)
    write_message("pubreftag %s" % pubreftag, verbose=9)

    # dict of recid -> institute_give_publ_id
    records_reports_numbers = citation_informations[0]
    # dict of recid -> ['astro-ph/xyz'..]
    references_report_numbers = citation_informations[1]
    # dict of recid -> publication_infos_in_its_bibliography
    references_journals = citation_informations[2]
    # dict of recid -> its publication inf
    records_journals = citation_informations[3]

    t1 = os.times()[4]

    write_message("Phase 0: temporarily remove changed records from " \
                  "citation dictionaries; they will be filled later")
    for somerecid in updated_recids:
        try:
            del citations[somerecid]
        except KeyError:
            pass
        try:
            del references[somerecid]
        except KeyError:
            pass

    write_message("Phase 1: d_references_report_numbers")
    # d_references_report_numbers: e.g 8 -> ([astro-ph/9889],[hep-ph/768])
    # meaning: rec 8 contains these in bibliography
    done = 0
    for thisrecid, refnumbers in references_report_numbers.iteritems():
        if done % 10 == 0:
            task_sleep_now_if_required()

        if done % 1000 == 0:
            mesg = "done %s of %s" % (done, len(references_report_numbers))
            write_message(mesg)
            task_update_progress("d_references_report_numbers " + mesg)

        done += 1

        for refnumber in (r for r in refnumbers if r):
            p = refnumber
            f = 'reportnumber'

            p = standardize_report_number(p)
            # Search for "hep-th/5644654 or such" in existing records
            recids = get_recids_matching_query(p, f)
            write_message("These match searching %s in %s: %s" % \
                                                    (p, f, recids), verbose=9)

            if recids:
                # the refered publication is in our collection, remove
                # from missing
                remove_from_missing(p)
            else:
                # it was not found so add in missing
                insert_into_missing(thisrecid, p)

            # TODO: if we match more than one record
            # either duplicate record or something else
            # Maybe we should alert admins selectively
            if len(recids) == 1:
                recid = list(recids)[0]

                remove_from_missing(p)

                if recid not in citations_weight:
                    citations_weight[recid] = 0

                # Append unless this key already has the item
                if thisrecid not in citations.setdefault(recid, []):
                    citations[recid].append(thisrecid)
                    citations_weight[recid] += 1
                if recid not in references.setdefault(thisrecid, []):
                    references[thisrecid].append(recid)

    mesg = "done fully"
    write_message(mesg)
    task_update_progress(mesg)

    t2 = os.times()[4]

    #try to find references based on 999C5s, like Phys.Rev.Lett. 53 (1986) 2285
    write_message("Phase 2: d_references_s (journals)")
    done = 0
    for thisrecid, refss in references_journals.iteritems():
        if done % 10 == 0:
            task_sleep_now_if_required()

        if done % 1000 == 0:
            mesg = "done %s of %s" % (done, len(references_journals))
            write_message(mesg)
            task_update_progress("d_references_s " + mesg)

        done += 1

        for refs in (r for r in refss if r):
            p = refs
            f = 'journal'

            recids = list(search_unit(p, f) - INTBITSET_OF_DELETED_RECORDS)
            write_message("These match searching %s in %s: %s" \
                                             % (p, f, recids), verbose=9)
            if recids:
                # the refered publication is in our collection, remove
                # from missing
                remove_from_missing(p)
            else:
                # it was not found so add in missing
                insert_into_missing(thisrecid, p)

            # check citation and reference for this..
            if len(recids) == 1:
                recid = list(recids)[0]
                # the above should always hold

                if recid not in citations_weight:
                    citations_weight[recid] = 0

                if thisrecid not in citations.setdefault(recid, []):
                    citations[recid].append(thisrecid)
                    citations_weight[recid] += 1
                if recid not in references.setdefault(thisrecid, []):
                    references[thisrecid].append(recid)

    mesg = "done fully"
    write_message(mesg)
    task_update_progress(mesg)

    t3 = os.times()[4]
    done = 0
    write_message("Phase 3: d_reports_numbers")
    # Search for stuff like CERN-TH-4859/87 in list of refs
    for thisrecid, reportcodes in records_reports_numbers.iteritems():
        if done % 10 == 0:
            task_sleep_now_if_required()

        if done % 1000 == 0:
            mesg = "done %s of %s" % (done, len(records_reports_numbers))
            write_message(mesg)
            task_update_progress("d_reports_numbers %s" % mesg)

        done += 1

        for reportcode in (r for r in reportcodes if r):
            if reportcode.startswith('arXiv'):
                std_reportcode = standardize_report_number(reportcode)
                report_pattern = r'^%s( *\[[a-zA-Z.-]*\])?' % \
                                                re.escape(std_reportcode)
                recids = get_recids_matching_query(report_pattern,
                                                   pubrefntag,
                                                   'r')
            else:
                recids = get_recids_matching_query(reportcode,
                                                   pubrefntag,
                                                   'e')
            for recid in recids:
                # normal checks..
                if thisrecid not in citations_weight:
                    citations_weight[thisrecid] = 0

                # normal updates
                if recid not in citations.setdefault(thisrecid, []):
                    citations_weight[thisrecid] += 1
                    citations[thisrecid].append(recid)
                if thisrecid not in references.setdefault(recid, []):
                    references[recid].append(thisrecid)

    mesg = "done fully"
    write_message(mesg)
    task_update_progress(mesg)

    # Find this record's pubinfo in other records' bibliography
    write_message("Phase 4: d_records_s")
    done = 0
    t4 = os.times()[4]
    for thisrecid, rec_journals in records_journals.iteritems():
        if done % 10 == 0:
            task_sleep_now_if_required()

        if done % 1000 == 0:
            mesg = "done %s of %s" % (done, len(records_journals))
            write_message(mesg)
            task_update_progress("d_records_s %s" % mesg)

        done += 1

        for journal in rec_journals:
            journal = journal.replace("\"", "")
            # Search the publication string like
            # Phys. Lett., B 482 (2000) 417 in 999C5s
            recids = search_unit(p=journal, f=pubreftag, m='a') \
                                                - INTBITSET_OF_DELETED_RECORDS
            write_message("These records match %s in %s: %s" \
                                   % (journal, pubreftag, recids), verbose=9)

            for recid in recids:
                # normal checks
                if thisrecid not in citations_weight:
                    citations_weight[thisrecid] = 0

                if recid not in citations.setdefault(thisrecid, []):
                    citations[thisrecid].append(recid)
                    citations_weight[thisrecid] += 1
                if thisrecid not in references.setdefault(recid, []):
                    references[recid].append(thisrecid)

    mesg = "done fully"
    write_message(mesg)
    task_update_progress(mesg)

    write_message("Phase 5: remove empty lists from dicts")

    # Remove empty lists in citation and reference
    keys = citations.keys()
    for k in keys:
        if not citations[k]:
            del citations[k]

    keys = references.keys()
    for k in keys:
        if not references[k]:
            del references[k]

    write_message("Phase 6: self-citations")
    # Get the initial self citation dict
    if not task_get_option("self-citations"):
        write_message("Self cite processing disabled." \
                      " Use --self-citations option to enable it.")
    else:
        write_message("self cite enabled")
        selfcites = get_self_citations(updated_recids,
                                     citations,
                                     references,
                                     selfcites,
                                     selfrefs,
                                     config)
    # selfdic consists of
    # key k -> list of values [v1,v2,..]
    # where k is a record with author A and k cites v1,v2.. and A appears in v1,v2..

    # create a reverse "x cited by y" self cit dict
    selfrefs = {}
    for k, vlist in selfcites.iteritems():
        for v in vlist:
            selfrefs.setdefault(v, set()).add(k)

    write_message("Getting author citations")

    # Get author citations for records in updated_rec_list
    acit = task_get_option("author-citations")
    if not acit:
        print "Author cites disabled. Use -A option to enable it."
    else:
        write_message("author citations enabled")
        authorcites = get_author_citations(updated_recids, citations,
                                            authorcites, config)

    write_message("Phase 7: fill self-citations table")
    if not task_get_option("db-self-citations"):
        write_message("Self cite caching disabled." \
                      " Use --db-self-citations option to enable it.")
    else:
        prepare_self_citations_cache(updated_recids, references)

    if task_get_task_param('verbose') >= 3:
        # print only X first to prevent flood
        tmpdict = dict(islice(citations.iteritems(), 10))
        write_message("citation_list (x is cited by y): %s" % tmpdict)
        write_message("size: %s" % len(citations))
        tmpdict = dict(islice(references.iteritems(), 10))
        write_message("reference_list (x cites y): %s" % tmpdict)
        write_message("size: %s" % len(references))
        tmpdict = dict(islice(selfcites.iteritems(), 10))
        write_message("selfcitedbydic (x is cited by y and one of the " \
                      "authors of x same as y's): %s" % tmpdict)
        write_message("size: %s" % len(selfcites))
        tmpdict = dict(islice(selfrefs.iteritems(), 10))
        write_message("selfdic (x cites y and one of the authors of x " \
                      "same as y's): %s" % tmpdict)
        write_message("size: %s" % len(selfrefs))
        tmpdict = dict(islice(authorcites.iteritems(), 10))
        write_message("authorcitdic (author is cited in recs): %s" % tmpdict)
        write_message("size: %s" % len(authorcites))

    t5 = os.times()[4]

    write_message("Execution time for analyzing the citation information " \
                  "generating the dictionary:")
    write_message("... checking ref number: %.2f sec" % (t2-t1))
    write_message("... checking ref ypvt: %.2f sec" % (t3-t2))
    write_message("... checking rec number: %.2f sec" % (t4-t3))
    write_message("... checking rec ypvt: %.2f sec" % (t5-t4))
    write_message("... total time of ref_analyze: %.2f sec" % (t5-t1))

    return citations_weight, citations, references, selfcites, \
                                                        selfrefs, authorcites


def insert_cit_ref_list_intodb(citation_dic, reference_dic, selfcbdic,
                               selfdic, authorcitdic):
    """Insert the reference and citation list into the database"""
    insert_into_cit_db(reference_dic, "reversedict")
    insert_into_cit_db(citation_dic, "citationdict")
    insert_into_cit_db(selfcbdic, "selfcitedbydict")
    insert_into_cit_db(selfdic, "selfcitdict")

    for a in authorcitdic.keys():
        lserarr = serialize_via_marshal(authorcitdic[a])
        # author name: replace " with something else
        a.replace('"', '\'')
        a = unicode(a, 'utf-8')
        try:
            ablob = run_sql("SELECT hitlist FROM rnkAUTHORDATA WHERE aterm = %s", (a,))
            if not (ablob):
                run_sql("INSERT INTO rnkAUTHORDATA(aterm,hitlist) VALUES (%s,%s)",
                         (a, lserarr))
            else:
                run_sql("UPDATE rnkAUTHORDATA SET hitlist  = %s WHERE aterm=%s",
                        (lserarr, a))
        except:
            register_exception(prefix="could not read/write rnkAUTHORDATA aterm=%s hitlist=%s" % (a, lserarr), alert_admin=True)


def insert_into_cit_db(dic, name):
    """an aux thing to avoid repeating code"""
    ndate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    try:
        s = serialize_via_marshal(dic)
        write_message("size of %s %s" % (name, len(s)))
        # check that this column really exists
        testres = run_sql("SELECT object_name FROM rnkCITATIONDATA WHERE object_name = %s",
                       (name,))
        if testres:
            run_sql("UPDATE rnkCITATIONDATA SET object_value = %s where object_name = %s",
                    (s, name))
        else:
            # there was no entry for name, let's force..
            run_sql("INSERT INTO rnkCITATIONDATA(object_name,object_value) values (%s,%s)",
                     (name, s))
        run_sql("UPDATE rnkCITATIONDATA SET last_updated = %s where object_name = %s",
               (ndate, name))
    except:
        register_exception(prefix="could not write "+name+" into db", alert_admin=True)


def get_cit_dict(name):
    """get a named citation dict from the db"""
    cdict = {}
    try:
        cdict = run_sql("SELECT object_value FROM rnkCITATIONDATA WHERE object_name = %s",
                       (name,))
        if cdict and cdict[0] and cdict[0][0]:
            dict_from_db = deserialize_via_marshal(cdict[0][0])
            return dict_from_db
        else:
            return {}
    except:
        register_exception(prefix="could not read "+name+" from db", alert_admin=True)
        return {}


def get_initial_author_dict():
    """read author->citedinlist dict from the db"""
    adict = {}
    try:
        ah = run_sql("SELECT aterm,hitlist FROM rnkAUTHORDATA")
        for (a, h) in ah:
            adict[a] = deserialize_via_marshal(h)
        return adict
    except:
        register_exception(prefix="could not read rnkAUTHORDATA", alert_admin=True)
        return {}


def insert_into_missing(recid, report):
    """put the referingrecordnum-publicationstring into
       the "we are missing these" table"""
    report.replace('"', '\'')
    try:
        srecid = str(recid)
        wasalready = run_sql("""SELECT id_bibrec
                                FROM rnkCITATIONDATAEXT
                                WHERE id_bibrec = %s
                                AND extcitepubinfo = %s""",
                              (srecid, report))
        if not wasalready:
            run_sql("""INSERT INTO rnkCITATIONDATAEXT(id_bibrec, extcitepubinfo)
                       VALUES (%s,%s)""",
                   (srecid, report))
    except:
        # we should complain but it can result to million lines of warnings so just pass..
        pass


def remove_from_missing(report):
    """remove the recid-ref -pairs from the "missing" table for report x: prob
       in the case ref got in our library collection"""
    report.replace('"', '\'')
    run_sql("""DELETE FROM rnkCITATIONDATAEXT
               WHERE extcitepubinfo = %s""", (report,))


def create_analysis_tables():
    """temporary simple table + index"""
    sql1 = "CREATE TABLE IF NOT EXISTS tmpcit (citer mediumint(10), cited mediumint(10)) TYPE=MyISAM"
    sql2 = "CREATE UNIQUE INDEX citercited on tmpcit(citer, cited)"
    sql3 = "CREATE INDEX citer on tmpcit(citer)"
    sql4 = "CREATE INDEX cited on tmpcit(cited)"
    try:
        run_sql(sql1)
        run_sql(sql2)
        run_sql(sql3)
        run_sql(sql4)
    except:
        pass


def write_citer_cited(citer, cited):
    """write an entry to tmp table"""
    sciter = str(citer)
    scited = str(cited)
    try:
        run_sql("INSERT INTO tmpcit(citer, cited) VALUES (%s,%s)", (sciter, scited))
    except:
        pass


def print_missing(num):
    """
    Print the contents of rnkCITATIONDATAEXT table containing external
    records that were cited by NUM or more internal records.

    NUM is by default taken from the -E command line option.
    """
    if not num:
        num = task_get_option("print-extcites")

    write_message("Listing external papers cited by %i or more internal records:" % num)

    res = run_sql("SELECT COUNT(id_bibrec), extcitepubinfo FROM rnkCITATIONDATAEXT \
                   GROUP BY extcitepubinfo HAVING COUNT(id_bibrec) >= %s \
                   ORDER BY COUNT(id_bibrec) DESC", (num,))
    for (cnt, brec) in res:
        print str(cnt)+"\t"+brec

    write_message("Listing done.")


def tagify(parsedtag):
    """aux auf to make '100__a' out of ['100','','','a']"""
    tag = ""
    for t in parsedtag:
        if t == '':
            t = '_'
        tag = tag+t
    return tag
