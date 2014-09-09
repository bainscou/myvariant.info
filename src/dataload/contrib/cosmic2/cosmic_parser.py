# -*- coding: utf-8 -*-
import csv
import re
import glob


VALID_COLUMN_NO = 29


# remove keys whos values are "."
# and remove empty dictionaries
def dict_sweep(d):
    for key, val in d.items():
        if val == "":
            del d[key]
        elif isinstance(val, dict):
            dict_sweep(val)
            if len(val) == 0:
                del d[key]
    return d


# convert string numbers into integers or floats
def value_convert(d):
    for key, val in d.items():
        try:
            d[key] = int(val)
        except (ValueError, TypeError):
            try:
                d[key] = float(val)
            except (ValueError, TypeError):
                pass
        if isinstance(val, dict):
            value_convert(val)
    return d


# convert one snp to json
def _map_line_to_json(fields):
    chr_info = re.findall(r"[\w']+", fields[17])
    chrom = chr_info[0]  # Mutation GRCh37 genome position
    chromStart = int(chr_info[1])
    chromEnd = int(chr_info[2])

    HGVS = None
    cds = fields[13]
    sub = re.search(r'[ATCG]+>[ATCGMN]+', cds)
    ins = re.search(r'ins[ATCGMN]+|ins[0-9]+', cds)
    delete = re.search('del', cds)
    del_ins = re.search(r'[0-9]+>[ATCGMN]+', cds)
    comp = re.search(r'[ATCGMN]+', cds)

    if sub:
        HGVS = "chr%s:g.%d%s" % (chrom, chromStart, sub.group())
    elif ins:
        HGVS = "chr%s:g.%d_%d%s" % (chrom, chromStart, chromEnd, ins.group())
    elif delete:
        HGVS = "chr%s:g.%d_%ddel" % (chrom, chromStart, chromEnd)
    elif del_ins:
        HGVS = "chr%s:g.%d_%ddelins%s" % (chrom, chromStart, chromEnd, comp.group())
    else:
        print 'Error2:', fields[15], cds

    # load as json data
    if HGVS is None:
        return

    one_snp_json = {

        "_id": HGVS,
        "cosmic":
            {
                "gene":
                    {
                        "symbol": fields[0],  # Gene name
                        "id": fields[3],  # HGNC ID
                        "cds_length": fields[2]
                    },
                "transcript": fields[1],  # Accession Number
                "sample":
                    {
                        "name": fields[4],  # Sample name
                        "id": fields[5]  # ID_sample
                    },
                "tumour":
                    {
                        "id": fields[6],  # ID_tumour
                        "primary_site": fields[7],  # Primary site
                        "site_subtype": fields[8],  # Site subtype
                        "primary_histology": fields[9],  # Primary histology
                        "histology_subtype": fields[10],  # Histology subtype
                        "origin": fields[1]
                    },
                "mutation":
                    {
                        "id": fields[12],  # Mutation ID
                        "cds": cds,  # Mutation CDS
                        "aa": fields[14],  # Mutation AA
                        "description": fields[15],  # Mutation Description
                        "zygosity": fields[16],  # Mutation zygosity
                        "somatic_status": fields[21]  # Mutation somatic status
                    },
                "chrom": chrom,
                "hg19":
                   {
                        "start": chromStart,
                        "end": chromEnd
                    },
                "pubmed": fields[22]  # Pubmed_PMID
            }
        }
    return dict_sweep(value_convert(one_snp_json))


# open file, parse, pass to json mapper
def data_generator(input_file):
    open_file = open(input_file)
    cosmic = csv.reader(open_file, delimiter="\t")
    cosmic.next()  # skip header
    for row in cosmic:
        assert len(row) == VALID_COLUMN_NO
        if row[13].find('?') != -1 or \
           row[16] == "" or \
           row[17] == "":  # Mutation GRCh37 genome position, Mutation CDS
            continue  # skip variant
        one_snp_json = _map_line_to_json(row)
        if one_snp_json:
            yield one_snp_json
    open_file.close()


# load path and find files, pass to data_generator
def load_data(path):
    for input_file in sorted(glob.glob(path)):
        print input_file
        data = data_generator(input_file)
        for one_snp_json in data:
            yield one_snp_json
