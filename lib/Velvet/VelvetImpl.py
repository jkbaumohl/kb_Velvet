# -*- coding: utf-8 -*-
#BEGIN_HEADER
# The header block is where all import statments should live
import os
from Bio import SeqIO
from pprint import pprint, pformat
from AssemblyUtil.AssemblyUtilClient import AssemblyUtil
from KBaseReport.KBaseReportClient import KBaseReport

from pprint import pformat, pprint
import time

#END_HEADER


class Velvet:
    '''
    Module Name:
    Velvet

    Module Description:
    A KBase module: Velvet

This is a KBase module that wraps the open source package "Short read de novo assembler using de Bruijn graphs"
Version 1.2.10

References:
https://github.com/dzerbino/velvet
https://github.com/dzerbino/velvet/blob/master/Columbus_manual.pdf
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = "https://github.com/kbaseapps/Velvet.git"
    GIT_COMMIT_HASH = "f9dd477aaf7d370fb238d63483ed4dd3e6856f64"

    #BEGIN_CLASS_HEADER
    # Class variables and functions can be defined in this block
    #/kb/deployment/bin/velveth or velvetg
    VELVETH = '/kb/module/velvet/velveth'
    VELVETG = '/kb/module/velvet/velvetg'

    def log(self, message, prefix_newline=False):
            print(('\n' if prefix_newline else '') +
                          str(time.time()) + ': ' + str(message))

    def process_params(self, params):
        if 'workspace_name' not in params:
            raise ValueError('a string reprsenting workspace_name parameter is required')
        if 'out_folder' not in params:
            raise ValueError('a string reprsenting out_folder parameter is required')
        if 'hash_length' not in params:
            raise ValueError('an integerreprsenting  hash_length parameter is required')
        if 'hash_length' in params:
            if not isinstance(params['hash_length'], int):
                raise ValueError('hash_length must be of type int')
        if 'reads_channels' not in params:
            raise ValueError('key-val pairs representing the reads_channels parameter is required')
        if type(params['reads_channels']) != list:
            raise ValueError('reads_channels must be a list')
        for rc in params['reads_channels']:
            self.log('Read file channel info :\n' + pformat(rc))

    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR

        # Any configuration parameters that are important should be parsed and
        # saved in the constructor.
        self.cfg = config
        self.callbackURL = os.environ['SDK_CALLBACK_URL']
        self.log('Callback URL: ' + self.callbackURL)
        self.workspaceURL = config['workspace-url']
        self.scratch = os.path.abspath(config['scratch'])
        if not os.path.exists(self.scratch):
            os.makedirs(self.scratch)

        #END_CONSTRUCTOR
        pass


    def run_velveth(self, ctx, params):
        """
        Definition of run_velveth
        :param params: instance of type "VelvethParams" -> structure:
           parameter "out_folder" of String, parameter "workspace_name" of
           String, parameter "hash_length" of Long, parameter
           "reads_channels" of list of type "ReadsChannel" -> structure:
           parameter "read_type" of String, parameter "file_format" of
           String, parameter "read_file_info" of type "ReadFileInfo" (Define
           a structure that holds the read file name and its use. Note: only
           read_file_name is required, the rest are optional. e.g.,
           {"reference_file" => "test_reference.fa", "read_file_name" =>
           "mySortedReads.sam", "left_file" => "left.fa", "right_file" =>
           "right.fa"}) -> structure: parameter "read_file" of String,
           parameter "reference_file" of String, parameter "left_file" of
           String, parameter "right_file" of String, parameter "file_layout"
           of String
        :returns: instance of type "VelvetResults" (Output parameter(s) for
           run_velveth and run_velvetg report_name - the name of the
           KBaseReport.Report workspace object. report_ref - the workspace
           reference of the report.) -> structure: parameter "report_name" of
           String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_velveth
        self.log('Running run_velveth with params:\n' + pformat(params))

        token = ctx['token']

        # STEP 1: basic parameter checks + parsing
        self.process_params(params)

        # STEP 2: get the reads channels as reads file info
        out_folder = params['out_fodler']
        hash_length = params['hash_length']
        wsname = params['workspace_name']
        reads_channels = params['reads_channels']

        #print('Input reads file:' + file_name + '\nwith file format of ' + file_format + '\nand read type of ' + read_type)

        # STEP 3: run velveth
        # construct the command
        velveth_cmd = [self.MEGAHITH]

        # set the output location
        timestamp = int((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds() * 1000)
        output_dir = os.path.join(self.scratch, out_folder)
        #velveth_cmd.append('-o')
        velveth_cmd.append(output_dir)
        velveth_cmd.append(hash_length)

        velveth_cmd.append(out_folder)
        for rc in reads_channels:
            velveth_cmd.append('-' + rc[file_format])
            read_type = rc['read_type']
            velveth_cmd.append('-' + read_type)
            if(read_type == 'reference'):
                velveth_cmd.append(rc['read_file_info']['reference_file'])

            if(rc['file_layout'] == 'separate'):
                velveth_cmd.append('-' + rc['file_layout'])
                velveth_cmd.append(rc['read_file_info']['left_file'])
                velveth_cmd.append(rc['read_file_info']['right_file'])
            else:
                velveth_cmd.append(rc['read_file_info']['read_file'])


        # run velveth
        print('running velveth:')
        print('    ' + ' '.join(velveth_cmd))
        p = subprocess.Popen(velveth_cmd, cwd=self.scratch, shell=False)
        retcode = p.wait()

        print('Return code: ' + str(retcode))
        if p.returncode != 0:
            raise ValueError('Error running VELVETH, return code: ' + str(retcode) + '\n')

        output_contigs = os.path.join(output_dir, 'final.contigs.fa')

        # STEP 4: save the resulting assembly
        assemblyUtil = AssemblyUtil(self.callbackURL)
        output_data_ref = assemblyUtil.save_assembly_from_fasta({
                'file': {'path': output_contigs},
                'workspace_name': params['workspace_name'],
                'assembly_name': params['output_contigset_name']
                })

        # STEP 5: generate and save the report
        # compute a simple contig length distribution for the report
        lengths = []
        for seq_record in SeqIO.parse(output_contigs, 'fasta'):
            lengths.append(len(seq_record.seq))

        report = ''
        report += 'ContigSet saved to: ' + params['workspace_name'] + '/' + params['output_contigset_name'] + '\n'
        report += 'Assembled into ' + str(len(lengths)) + ' contigs.\n'
        report += 'Avg Length: ' + str(sum(lengths) / float(len(lengths))) + ' bp.\n'


        print('Saving report')
        kbr = KBaseReport(self.callbackURL)
        try:
            report_info = kbr.create_extended_report(
                {'message': report,
                 'objects_created': [{'ref': output_data_ref, 'description': 'Assembled contigs'}],
                 'direct_html_link_index': 0,
                 'html_links': [{'shock_id': quastret['shock_id'],
                                 'name': 'report.html',
                                 'label': 'VELVETH report'}
                                ],
                 'report_object_name': 'kb_velveth_report_' + str(uuid.uuid4()),
                 'workspace_name': params['workspace_name']
                 })
        except _RepError as re:
            # not really any way to test this, all inputs have been checked earlier and should be ok 
            print('Logging exception from creating report object')
            print(str(re))
            raise

        # STEP 6: contruct the output to send back
        output = {'report_name': report_info['name'], 'report_ref': report_info['ref']}
        #END run_velveth

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_velveth return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def run_velvetg(self, ctx, params):
        """
        Definition of run_velvetg
        :param params: instance of type "VelvetgParams" (Arguments for
           run_velvetg wk_folder                       : working directory
           name Standard options: -cov_cutoff <floating-point|auto>       :
           removal of low coverage nodes AFTER tour bus or allow the system
           to infer it (default: no removal) -ins_length <integer>          
           : expected distance between two paired end reads (default: no read
           pairing) -read_trkg <yes|no>             : tracking of short read
           positions in assembly (default: no tracking) -min_contig_lgth
           <integer>      : minimum contig length exported to contigs.fa file
           (default: hash length * 2) -amos_file <yes|no>             :
           export assembly to AMOS file (default: no export) -exp_cov
           <floating point|auto>  : expected coverage of unique regions or
           allow the system to infer it (default: no long or paired-end read
           resolution) -long_cov_cutoff <floating-point>: removal of nodes
           with low long-read coverage AFTER tour bus (default: no removal)
           Advanced options: -ins_length* <integer>          : expected
           distance between two paired-end reads in the respective short-read
           dataset (default: no read pairing) -ins_length_long <integer>     
           : expected distance between two long paired-end reads (default: no
           read pairing) -ins_length*_sd <integer>       : est. standard
           deviation of respective dataset (default: 10% of corresponding
           length) [replace '*' by nothing, '2' or '_long' as necessary]
           -scaffolding <yes|no>           : scaffolding of contigs used
           paired end information (default: on) -max_branch_length <integer> 
           : maximum length in base pair of bubble (default: 100)
           -max_divergence <floating-point>: maximum divergence rate between
           two branches in a bubble (default: 0.2) -max_gap_count <integer>  
           : maximum number of gaps allowed in the alignment of the two
           branches of a bubble (default: 3) -min_pair_count <integer>      
           : minimum number of paired end connections to justify the
           scaffolding of two long contigs (default: 5) -max_coverage
           <floating point>  : removal of high coverage nodes AFTER tour bus
           (default: no removal) -coverage_mask <int>    : minimum coverage
           required for confident regions of contigs (default: 1)
           -long_mult_cutoff <int>         : minimum number of long reads
           required to merge contigs (default: 2) -unused_reads <yes|no>     
           : export unused reads in UnusedReads.fa file (default: no)
           -alignments <yes|no>            : export a summary of contig
           alignment to the reference sequences (default: no) -exportFiltered
           <yes|no>        : export the long nodes which were eliminated by
           the coverage filters (default: no) -clean <yes|no>                
           : remove all the intermediary files which are useless for
           recalculation (default : no) -very_clean <yes|no>            :
           remove all the intermediary files (no recalculation possible)
           (default: no) -paired_exp_fraction <float>   : remove all the
           paired end connections which less than the specified fraction of
           the expected count (default: 0.1) -shortMatePaired* <yes|no>     
           : for mate-pair libraries, indicate that the library might be
           contaminated with paired-end reads (default no) -conserveLong
           <yes|no>          : preserve sequences with long reads in them
           (default no) Output: wk_folder/contigs.fa            : fasta file
           of contigs longer than twice hash length wk_folder/stats.txt      
           : stats file (tab-spaced) useful for determining appropriate
           coverage cutoff wk_folder/LastGraph             : special
           formatted file with all the information on the final graph
           wk_folder/velvet_asm.afg        : (if requested) AMOS compatible
           assembly file Example: ./velvetg wk_folder [options] string
           wk_folder; #folder name for files to work on and to save results
           float cov_cutoff; #removal of low coverage nodes AFTER tour bus or
           allow the system to infer it (default: no removal) int ins_length;
           #expected distance between two paired end reads (default: no read
           pairing) int read_trkg; # (1=yes|0=no) tracking of short read
           positions in assembly (default:0) int min_contig_length; #minimum
           contig length exported to contigs.fa file (default: hash length *
           2) int amos_file; # (1=yes|0=no) #export assembly to AMOS file
           (default: 0) float exp_cov; # <floating point|auto>, expected
           coverage of unique regions or allow the system to infer it
           (default: no long or paired-end read resolution) float
           long_cov_cutoff; #removal of nodes with low long-read coverage
           AFTER tour bus(default: no removal)) -> structure: parameter
           "workspace_name" of String, parameter "wk_folder" of String,
           parameter "cov_cutoff" of Double, parameter "ins_length" of Long,
           parameter "read_trkg" of Long, parameter "min_contig_length" of
           Long, parameter "amos_file" of Long, parameter "exp_cov" of
           Double, parameter "long_cov_cutoff" of Double
        :returns: instance of type "VelvetResults" (Output parameter(s) for
           run_velveth and run_velvetg report_name - the name of the
           KBaseReport.Report workspace object. report_ref - the workspace
           reference of the report.) -> structure: parameter "report_name" of
           String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_velvetg
        #END run_velvetg

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_velvetg return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
