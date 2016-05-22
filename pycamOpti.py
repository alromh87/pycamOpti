#!/usr/bin/python
"USAGE: pycamOpti.py <file>"

import sys

file_in_name      = ''

G_modal           = 0
G_dest            = 0
X_dest            = 0
Y_dest            = 0
Z_dest            = 1
M_dest            = 0
T_dest            = 0

G_modal_codes     = [0,1,81]
G_codes_probing   = [1,81]

class Coordinate():
    def __init__(self,X,Y,Z):
        self.X = X
        self.Y = Y
        self.Z = Z

class MillTrayectory():
    def __init__(self, first):
        self.first = first
        self.last  = first
        self.lines = []
        self.post  = []

    def connects(self, next):
        if self.last.X == next.first.X and self.last.Y == next.first.Y:
            if self.last.Z != next.first.Z:
                return 1
            else:
                return 2    
        return 0

def get_num(line,char_ptr,num_chars):
    char_ptr=char_ptr+1
    numstr = ''
    good   = '-.0123456789'
    while char_ptr < num_chars:
        digit = line[char_ptr]
        if good.find(digit) != -1:
           numstr = numstr + digit
           char_ptr = char_ptr + 1
        else: break
    return numstr

if __name__=='__main__':
    if len(sys.argv) != 2:            
        print __doc__
    else:
        file_in_name = sys.argv[1]
        file_in        = []
        file_out       = []
        intro          = []
        trayectories   = []
        numstr         = ''
        char           = ''
        in_trayectorie = False

        f = open(file_in_name, 'r')
        for line in f:
            file_in.append(line)
        f.close()

        # parse each line
        line_ptr=0
        num_lines=len(file_in)
        while line_ptr < num_lines:
            line = file_in[line_ptr]
            X_start = X_dest
            Y_start = Y_dest
            Z_start = Z_dest
        
            # parse each character
            char_ptr = 0
            num_chars= len(line)
            coord_count = 0
            G_found     = False
            while char_ptr < num_chars:
                char = line[char_ptr]      
                if '('.find(char) != -1:
                    break
                elif ';'.find(char) != -1:
                    line = line.replace(';','(',1).replace('\n',')\n',1)
                    break
                elif char == 'G' :
                    G_dest = int(get_num(line,char_ptr,num_chars))
                    coord_count = coord_count+1
                    G_found = True
                elif char == 'X' :
                    X_dest = float(get_num(line,char_ptr,num_chars))
                    coord_count = coord_count+1
                elif char == 'Y' :
                    Y_dest = float(get_num(line,char_ptr,num_chars))
                    coord_count = coord_count + 1
                elif char == 'Z' :
                    Z_dest = float(get_num(line,char_ptr,num_chars))
                    coord_count = coord_count + 1
                elif char == 'R' :
                    R_dest = float(get_num(line,char_ptr,num_chars))
                elif char == 'F' :
                    F_dest = float(get_num(line,char_ptr,num_chars))
                elif char == 'M' :
                    M_dest = float(get_num(line,char_ptr,num_chars))
                elif char == 'T' :
                    T_dest = float(get_num(line,char_ptr,num_chars))

                char_ptr = char_ptr + 1

            if G_found:
                if G_dest in G_modal_codes:
                    G_modal = G_dest
            else:
                if coord_count > 0:
                    G_dest = G_modal

            if M_dest == 6:
                line = line.replace('\n', str(' G43 H%d\n' % T_dest))
                M_dest = -1

            if G_dest == 1 and Z_dest < Z_start:
                in_trayectorie = True
                coord = Coordinate(X_dest,Y_dest,Z_dest)
                newTray = MillTrayectory(coord)
                newTray.lines.append("(Iniciando nueva trayectoria en: "+ str(X_dest)+","+str(Y_dest)+","+str(Z_dest) +")\n")
                newTray.lines.append(line)
                trayectories.append(newTray)
                G_dest = -1
                line_ptr=line_ptr+1
                continue

            if in_trayectorie:
#TODO: mejorar logica de deteccion de ultimo punto de trayectoria
                if Z_dest > Z_start:
                    trayectories[-1].last = Coordinate(X_start,Y_start,Z_start)
                    trayectories[-1].lines.append("(Terminando trayectoria en:"+ str(X_start)+","+str(Y_start)+","+str(Z_start) +")\n")
                    in_trayectorie = False
                    trayectories[-1].post.append(line)
                else:
                    trayectories[-1].lines.append(line)
                G_dest = -1
            else:
                if trayectories != []:
                    trayectories[-1].post.append(line)
                else:
                    file_out.append(line)

            line_ptr=line_ptr+1

        #Ordenar trayectorias
        for i in xrange(0,len(trayectories)-1):
            for j in xrange(i+1,len(trayectories)):
                match = trayectories[i].connects(trayectories[j])
                #TODO: cambiar por case
                if match:
                    print i, ",", j
                    trayectories[i].post=[]
                    trayectories.insert(i+1, trayectories.pop(j))
                    if match == 1:
                        trayectories[i].post.append("Z"+str(trayectories[i+1].last.Z)+"\n")
#                    else:
#                    trayectories[i].post.append()
                    break

        for trayectory in trayectories:
            for line in trayectory.lines:
              file_out.append(line)
            for line in trayectory.post:
              file_out.append(line)

        # OK now output the G code intro
        # (define the variables, set up the probe subroutine, the etch subroutine and the code to probe the grid)
        from time import localtime, strftime
        line = "(pyCAMOpti:) \n"
        intro.append(line)
        line = "(Imported from:  " + file_in_name + " at " + strftime("%I:%M %p on %d %b %Y", localtime())+ ")\n"
        intro.append(line)

        # Finally, create and then save the output file
        file_out = intro + file_out

        file_name_suffix = "_opti.ngc"
        n = file_in_name.rfind(".")
        if n != -1:
            file_out_name = file_in_name[0:n] + file_name_suffix
        else: file_out_name = file_in_name + file_name_suffix

        f = open(file_out_name, 'w')
        for line in file_out:
            f.write(line)
        f.close()

