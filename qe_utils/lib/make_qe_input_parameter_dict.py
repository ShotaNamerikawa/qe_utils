import toml
import os
import re
from collections import OrderedDict
import numpy as np
from numpy.typing import NDArray
# usage:
# function(arg:NDArray[np.int64])


def parse_to_toml(lines,remove_lines:NDArray|None = None):
    """function to parse Input File Description in QE and convert it to a TOML format string.
    
    Parse Input File Description in https://www.quantum-espresso.org/Doc/INPUT_*.html.

    Parameters
    ----------
    lines : _type_
        lines from the first line Namelist appears to the last line of the last bl

    Returns
    -------
    _type_
        _description_
    """
    
    groups = OrderedDict()
    group_name = None
    current_block = None
    skip_lines = False
    iremove = None #
    remove_last_line = None
    
    # remove no need lines first.                

    for line in lines:
        if line.startswith('Namelist:') or line.startswith('Card:'):
            # Start of a new group
            if group_name and current_block:
                groups[group_name].append(current_block)
                
            parts = line.split()
            group_type = parts[0]
            group_name = parts[1]
            
            groups[group_name] = groups.get(group_name, [])
            current_block = []

        elif '[Back to Top]' in line:
            # End of a block
            if current_block:
                groups[group_name].append(current_block)
            current_block = []

        else:
            # Continue current block
            # First, remove no need lines.
                        
            if skip_lines == True:  
                if re.match(r"^ *{}.*".format(remove_last_line),line) is not None:
                    #When the last line of no need lines is found, skipping is stopped.
                    skip_lines = False
                    remove_last_line = None
                    continue

            else:
                skip_1_line = False
                
                #check wheter line is needed.
                if re.match(r"^ *\n",line) is not None:
                    #remove empty lines
                    skip_1_line = True
                else:
                    for i,rline in enumerate(remove_lines[:,0]):
                        if re.match(r"^ *{}.*".format(rline),line) is not None:
                            if remove_lines[i,1] != "":
                                iremove = i
                                remove_last_line = str(remove_lines[iremove,1])
                                skip_lines = True
                            skip_1_line = True
                            break
                        
                if skip_1_line == True:
                    skip_1_line == False #skip 1 line                
                        
                elif current_block is not None:
                    current_block.append(line)

    if group_name and current_block:
        groups[group_name].append(current_block)

    # Convert parsed data to TOML format
    toml_data = OrderedDict()
    for group, blocks in groups.items():
        toml_data[group] = OrderedDict()
        for block in blocks:
            if not block:
                continue
            first_line = [parameter_or_type.strip() for parameter_or_type in block[0].split()]
            if "Card's" in first_line[0]:
                #Card's options is exceptional block.
                key = "Card's options"
                toml_data[group][key] = OrderedDict()
                toml_data[group][key]["options"] = list(filter(lambda x: x != "|", first_line[1:]))
            else:
                key = " ".join(first_line[0:-1])
                type_key = first_line[-1].strip()
                toml_data[group][key] = OrderedDict()
                toml_data[group][key]["type"] = type_key
                
            for line in block[1:]:
                if line.startswith('Default:'):
                    toml_data[group][key]['default'] = line.split()[1].strip("'")
                elif line.startswith('Status:'):
                    toml_data[group][key]['status'] = line.split()[1]

    return toml.dumps(toml_data)

if __name__ == "__main__":
    # example for https://www.quantum-espresso.org/Doc/INPUT_PW.html#idm1676
    input_file = os.path.join(os.getenv("HOME"),"Documents/ChatGPT_prompt_and_files","QE_pwx_input")
    
    # To obtain toml correctly, these lines (or block of lines) must be removed.
    removed_lines = np.array([
        ["Either:",""],
        ["Or:",""],
        ["variables used only if gate = .TRUE.",""],
        ["variables used for molecular dynamics",""],
        ["keywords used only in BFGS calculations",""],
        ["keywords used only in the FIRE minimization algorithm",""],
        ["input this namelist only if calculation == 'vc-relax' or 'vc-md'",""],
        ["Input this namelist only if lfcp = .TRUE.",""],
        ["Variables used for FCP dynamics.",""],
        ["Input this namelist only if trism = .TRUE.",""],
        ["Syntax:","Description of items:"],
        ["IF DFT+U :","Description of items:"],
        ["IF tpiba OR crystal OR tpiba_b OR crystal_b OR tpiba_c OR crystal_c :","Description of items:"],
        ["IF calculation == 'bands' OR calculation == 'nscf' :","Description of items:"],
        ["Optional card","Description of items:"] 
    ])

    with open(input_file) as fp:
        file_content = fp.readlines()

    # Parse the content and convert to TOML format
    toml_output = parse_to_toml(file_content, remove_lines=removed_lines)

    # Save the TOML output to a file
    output_path = 'QE_INPUT_PW.toml'
    with open(output_path, 'w') as file:
        file.write(toml_output)