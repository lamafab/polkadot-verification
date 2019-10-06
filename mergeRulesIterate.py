#!/usr/bin/env python3

import os
import sys
from translateCoverage import *
from mergeRules        import *

# TODO: This is a needed hack because currently `--coverage-file` isn't respected by `krun`
def delete_coverage_files(src_definition_dir, main_defn_file):
    for (dirpath, dirnames, filenames) in os.fwalk(src_definition_dir + '/' + main_defn_file + '-kompiled'):
        for filename in filenames:
            if filename.endswith('_coverage.txt'):
                os.remove(dirpath + '/' + filename)

def get_coverage(input_program_path, src_definition_dir, main_defn_file, dst_definition_dir):
    delete_coverage_files(src_definition_dir, main_defn_file)
    (rc, stdout, _) = pyk.krun(src_definition_dir, input_program_path, kRelease = 'deps/wasm-semantics/deps/k/k-distribution/target/release/k')
    if not rc == 0:
        _fatal('Non-zero return code executing program!')
    coverage_file = None
    for (dirpath, dirnames, filenames) in os.fwalk(src_definition_dir + '/' + main_defn_file + '-kompiled'):
        for filename in filenames:
            if filename.endswith('_coverage.txt'):
                coverage_file = dirpath + '/' + filename
                break
    return translateCoverageFromPaths(src_definition_dir + '/' + main_defn_file + '-kompiled', dst_definition_dir + '/' + main_defn_file + '-kompiled', coverage_file)

def append_module_to_file(definition_dir, main_defn_file, main_module, iteration_number, new_rules, symbol_table):
    module_import = main_module if iteration_number == 0 else main_module + '-' + str(iteration_number - 1)
    new_module = KModule(main_module + '-' + str(iteration_number), [module_import], new_rules)
    new_module_str = pyk.prettyPrintKast(new_module, symbol_table)
    APPEND_TO_FILE(definition_dir + '/' + main_defn_file + '.k', new_module_str)

def iterated_compile(src_definition_dir, dst_definition_dir, main_defn_file, main_module, input_program, subsequence_length, iterations):
    src_definition_json = pyk.kastReadTerm(src_definition_dir + '/' + main_defn_file + '-kompiled/compiled.json')
    dst_definition_json = pyk.kastReadTerm(dst_definition_dir + '/' + main_defn_file + '-kompiled/compiled.json')

    src_symbol_table = pyk.buildSymbolTable(src_definition_json)
    dst_symbol_table = pyk.buildSymbolTable(dst_definition_json)

    for i in range(iterations):
        kompile_definition(src_definition_dir, main_defn_file, main_module)
        kompile_definition(dst_definition_dir, main_defn_file, main_module)
        coverage_data = get_coverage(input_program, src_definition_dir, main_defn_file, dst_definition_dir)
        merged_rules = mergeRules(coverage_data, dst_definition_json, main_defn_file, main_module, dst_symbol_table, subsequence_length = subsequence_length)
        append_module_to_file(src_definition_dir, main_defn_file, main_module, i, merged_rules, src_symbol_table)
        append_module_to_file(dst_definition_dir, main_defn_file, main_module, i, merged_rules, dst_symbol_table)

if __name__ == '__main__':
    src_definition_dir = sys.argv[0]      # .build/defn/coverage/llvm
    dst_definition_dir = sys.argv[1]      # .build/defn/kwasm/haskell
    main_defn_file     = sys.argv[2]      # wasm-with-k-term
    main_module        = sys.argv[3]      # WASM-WITH-K-TERM
    input_program      = sys.argv[4]      # deps/wasm-semantics/tests/simple/constants.wast
    subsequence_length = int(sys.argv[5]) # 2
    iterations         = int(sys.argv[6]) # 5

    iterated_compile(src_definition_dir, dst_definition_dir, main_defn_file, main_module, input_program, subsequence_length, iterations)
