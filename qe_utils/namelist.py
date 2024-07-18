import re
class NameList:
    """read namelist from file.
    
    Attributes
    ----------
    non_namelist_lines: List[str]
        lines including strings not able to be parsed into namelists.
    """
    def __init__(self,file:str):
        self.file = file
        self.read()
        
    def read(self):
        self.namelist = dict() #namelist[card_name] = dict(key1->value1,...)
        non_namelist_lines = None #lines which are not cards.
        in_card = False # whether line is in card.
        
        with open(self.file) as fp:
            lines = fp.readlines()
            
        for i,line in enumerate(lines):
            line = line.strip()
            if re.match("^ *&",line) is not None:
                in_card = True
                card_name = line
                self.namelist[card_name] = dict()
                continue
                
            elif re.match("^ */",line) is not None:
                in_card = False
                continue
    
            elif in_card == False:
                non_namelist_lines = lines[i:]
                break
            
            key_value = [key_or_value.strip() for key_or_value in line.split("=")]
            self.namelist[card_name][key_value[0]] = key_value[1]
            
        self.non_namelist_lines = non_namelist_lines # Non namelist lines.
            
                