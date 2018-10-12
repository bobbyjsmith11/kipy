from __future__ import print_function

"""
=============================
compare_boms.py
=============================
:Author: Jeff Porter
:Date:   2013
:Description:
    Tool for checking comparing two BOMs and reporting differences...
:Example:
>>> import compare_boms.py
>>> fileA = open("bomA.csv", 'rb')
>>> fileB = open("bomB.csv", 'rb')
>>> bomA = compare_boms.BOM(fileA)
>>> bomB = compare_boms.BOM(fileB)
>>> fo = open("ECO.csv", 'wb')
>>> lst = bomA.ECOtoList(bomB) #valuechg=True if you want to list value changes (False by default)
>>> for line in lst:
        fo.write(line + '/n')
>>> fo.close()


>>> python compare_boms.py --compare bom1.csv bom2.csv
>>>   >> generates text description of changes
>>> python compare_boms.py --eco eco.csv bom1.csv bom2.csv
>>>    >> generates eco.csv file with formatted list of updates to go from bom1.csv to bom2.csv


History:
26 Oct 2016:  A bunch of changes in importing BOMs.  In particular, it will now search for the apparent header row and
              start reading data following the header.  It seems to take the EPIQ TEMPLATE output from Alitum without
              too much grief.

              The --eco option now specifies the file name in which to store the change information.  csv.writer is used
              to make the file .csv compliant (handles commas in part descriptions!)

              When a part is flagged as "DNI" in its value or with a "Not Fitted" value under the "Fitted" column (if present),
              the manufacturer and part number will be set to "" and the value will be set to "DNI".

              Improved the handling of mixed reference designators on a single part number.  Previously, if a part number had
              reference designators with single and multicharacter alpha prefixes, an exception would be raised.

              Improved the handling of exceptions due to misunderstood (or badly formattted) BOM files.  The program will
              now attempt to provide some detail on where exactly things went wrong.

"""

import csv
import re

import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
class BadRefDes(Exception):
    pass


BOM_column_headings = { 'PartNumber' : ['Part Number', 'Manufacturer Part Number',
                                        'Manufacturer Part Number 1', 'PartNumber'],
                        'Manufacturer' : ['Manufacturer','MFG', 'Manufacturer 1'],
                        'Description' : ['Description','Desc'],
                        'Value' : ['Value'],
                        'Comment' : ['Comment'],
                        'RefDes' : ['Designator','RefDes','Ref Des'],
                        'Qty' : ['Qty','Quantity'],
                        'Fitted' : ['Fitted'] }

mfg_aliases = { 'TDK CORPORATION' : 'TDK',
                'SKYWORKS SOLUTIONS INC' : 'SKYWORKS',
                'PANASONIC ELECTRONIC COMPONENTS' : 'PANASONIC',
                'ON SEMICONDUCTOR' : 'ONSEMI',
                'MICRON TECHNOLOGY' : 'MICRON',
                'AVX' : 'KYOCERA',
                'INFINEON TECHNOLOGIES' : 'INFINEON',
                'HIROSE CONNECTOR' : 'HIROSE',
                'HIROSE ELECTRIC CO LTD' : 'HIROSE',
                'CYPRESS SEMICONDUCTOR' : 'CYPRESS',
                'COIL CRAFT' : 'COILCRAFT',
                'AVAGO TECHNOLOGIES' : 'AVAGO',
                'ANALOG DEVICES INC' : 'ANALOG',
                'ANALOG DEVICES INC.' : 'ANALOG',
                'ANALOG DEVICES' : 'ANALOG',
                'ABRACON CORPORATION' : 'ABRACON' }

def compare_mfg(a,b):
    def alias(x):
        return mfg_aliases.get(x.upper()) or x.upper()
    return alias(a) == alias(b)        
                
                
                

def run_bom_compare(bomA,bomB,eco_file):
    """
    """
    lst = bomA.ECOtoList(bomB)
    header = "action,ref,old manufacturer,old part number,old value,,new manufacturer,new part number,new value\n"
    eco_file.write(header)
    for line in lst:
        eco_file.write(line + '\n')
    eco_file.close()
    

def split_refdes_list(refs):
    out = []
    for r in refs.split(','):
        ref = r.strip()
        if r.find('-')>0:
            m = re.match('\s*([A-Z]+)(\d+)\s*-\s*([A-Z]+)(\d+)',r)
            if m:
                try:
                    r1,n1,r2,n2 = m.groups()
                    n1 = int(n1)
                    n2 = int(n2)
                except ValueError:
                    raise BadRefDes("ref des %s/%s doesn't have integer sequence number" % (r1,r2))
                if n2<=n1 or n2-n1>1000 or r1!=r2:
                    raise BadRefDes("ref des sequence %s-%s is not allowed" % (r1,r2))
            ref = ['%s%d' % (r1,n) for n in range(n1,n2+1)]
        else:
            if re.match(r"\s*([A-Za-z]+)(\d+)",r) is None:
                raise BadRefDes("No valid refdes found")
            ref = [ref]
        out.extend(ref)
    return sorted(out)


class RefDesList(frozenset):
    def __repr__(self):
        return ','.join(self.sorted())

    def sorted(self,reverse=False):
        """ return list of reference desginators sorted numerically (not ascii order) """
        #10/26/16 JWP: changed code to split each ref des individually
        r = list(self)
        for k in range(len(r)):
            m=re.match(r"([a-zA-Z]+)(\d+)",r[k])
            if m==None:
                raise BadRefDes("Ref Des %s doesn't have AAANNN format" % r[k])
            r[k] = m.groups()
        r.sort(key=lambda tup:(tup[0],int(tup[1])),reverse=reverse)
        return ["".join(x) for x in r]
    

class Part(object):
    def __init__(self,row,keys):
        """ create a part using the dictionary (row read from CSV file) and the mapping keys """

        self.manufacturer = row[keys.Manufacturer].upper()
        self.partnumber = row[keys.PartNumber].upper()
        self.desc = row.get(keys.Description) or ""
        self.value = row.get(keys.Value) or row.get(keys.Description) or ""
        if len(self.value)>0:
            self.value = self.value.upper()
        try:
            self.refs = RefDesList( split_refdes_list( row[keys.RefDes] ) )
        except BadRefDes as err:
            err.args = err.args + ("Bad reference designator format for %s/%s/%s/%s" % 
                (self.manufacturer,self.partnumber,self.desc,row[keys.RefDes]),)
            raise 
        self.quant = int(row[keys.Qty])


        if row.get(keys.Fitted) != 'Not Fitted':
            if self.quant != len(self.refs):
                print( "Warning:  Number of ref des (%d) for %s does not match quantity (%d)" % (len(self.refs),
                                                                                                self.partnumber,
                                                                                                self.quant))
        #if row.get(keys.Fitted)=='Not Fitted' and self.value=='':
        #    self.value = 'DNI'
        if row.get(keys.Fitted)=='Not Fitted' or self.value == 'DNI':
            if row.get(keys.Fitted)=='Fitted':
                eprint( "Warning:  Part %s is marked as Fitted but value is DNI" % self.partnumber)
            self.value = 'DNI'
            self.partnumber = ''
            self.manufacturer = ''
        

class BOMKeys(object):
    """ object that translates column headings for BOMs.  The
      following attributes are configured to be the proper column
      header:
      self.PartNumber - part number
      self.Manufacturer - manufacturer
      self.Value - value
      self.Comment - comment (Altium part number, should be duplicated in PN field)
      self.RefDes - ref des
      self.Qty - quantity
      self.Fitted - 'Fitted' or '' means installed, 'Not Fitted' means DNP
      """
    
    def __init__(self,row):
        for k,words in BOM_column_headings.iteritems():
            w_list = [x.upper() for x in words]
            for ndx in row:
                if ndx.upper() in w_list:
                    setattr(self,k,ndx)
                    break
            else:
                setattr(self,k,k)
   

class BOMReader(object):
    """
            Class that can read a CSV formatted BOM file.  The file should have a line containing
            Part Number, Manufacturer, RefDes, and Quantity header labels.  Lines before this
            header will be ignored.

            Otherwise this class works much like a DictReader()
            
            """
    def __init__(self,csvfile,**kwds):
        self.line_num = 0
        headers = self._find_header_row(csvfile)
        self.csv = csv.DictReader(csvfile,fieldnames=headers,**kwds)
        self.keys = BOMKeys( headers )

    def _is_heading_found_in_row(self,h,row):
        for alias in BOM_column_headings[h]:
            if alias in row:
                return True
        return False

    def _find_header_row(self,fi):
        required_columns = ['PartNumber','Manufacturer','RefDes','Qty']
        for row in csv.reader(fi):
            self.line_num += 1
            if all([self._is_heading_found_in_row(h,row) for h in required_columns]):
                return row
        raise Exception("Unable to locate BOM header row")

    def __iter__(self):
        return self
    
    def next(self):
        while True:
            try:
                self.line_num += 1
                return Part( self.csv.next(), self.keys )
            except BadRefDes as err:
                eprint( "Ignoring line %d due to invalid format: %s" % (self.line_num,err.args))

class BOM(object):
    def __init__(self,fi):
        """ create a BOM from a .CSV file object 
            each part number must occur only once.  """
        self.parts = list(BOMReader(fi))
        #check for duplicate parts
        sorted_list = sorted(self.parts, key=lambda a:a.partnumber)
        for k in range(len(sorted_list)-1):
            if sorted_list[k].partnumber != '' and (sorted_list[k].partnumber == sorted_list[k+1].partnumber):
                eprint("Warning:  BOM contains duplicate part number: %s" % sorted_list[k].partnumber)

    def findPart(self,attribute,value):
        for p in self.parts:
            if getattr(p,attribute)==value:
                return p
        raise ValueError
        
    def compare(self,newBom):
        """ Compare self to a new BOM object, printing out differences """
        checked=[]
        for p in self.parts:
            try:
                new_part = newBom.findPart('partnumber',p.partnumber)
            except ValueError:
                print("Missing part %s in new BOM / %s" % (p.partnumber,p.refs))
                continue
            checked.append(p.partnumber)
            if p.refs == new_part.refs:
                continue
            newr = new_part.refs - p.refs
            oldr = p.refs - new_part.refs
            if len(newr)>0:
                print( "Part %s: The new BOM       adds ref des %s" % (p.partnumber,newr)) #format_refs(newr))
            if len(oldr)>0:
                print( "Part %s: The new BOM is missing ref des %s" % (p.partnumber,oldr)) #format_refs(oldr))
        for p in newBom.parts:
            try:
                pp = self.findPart('partnumber',p.partnumber)
            except ValueError:
                print( "Old BOM is missing part %s / %s" % (p.partnumber,p.refs))

    def listByRefDes(self):
        """ return a dict mapping refdes to part numbers """
        d = {}
        for p in self.parts:
            for r in p.refs:
                if d.has_key(r):
                    raise Exception("Duplicate reference designator %s (P/Ns %s and %s)" %
                                    (r,p.partnumber, d[r].partnumber))
                d[r] = p
        return d
    
    def calculateECO(self,newBom):
        """ generate a list of changes to go from SELF to NewBOM """
        oldlist = self.listByRefDes()
        newlist = newBom.listByRefDes()

        difflist = []
        for ref,oldpart in oldlist.iteritems():
            try:
                newpart = newlist[ref]
            except KeyError:
                difflist.append( ('remove',ref,oldpart) )
                continue                
            if (newpart.partnumber!=oldpart.partnumber or
                not compare_mfg(newpart.manufacturer,oldpart.manufacturer) or
                newpart.value != oldpart.value):
                difflist.append( ('change',ref,oldpart,newpart) )
            del newlist[ref]

        for ref,newpart in newlist.iteritems():
            difflist.append( ('add',ref,newpart) )

        return difflist
                             
    def showECO(self,newBom, valuechg=False,outfile=None):
        if outfile is None:
            outfile = sys.stdout
        lst = self.ECOtoList(newBom,valuechg)
        fo = csv.writer(outfile)
        for txt in lst:
            fo.writerow( txt )
            
    def ECOtoList(self,newBom, valuechg=False):
        def sort_part_list(part_list,k):
            # part_list is a list of tuples
            # k is which tuple index has the part (.value/.partnumber/.manufacturer) 
            s = sorted(part_list, cmp=lambda x,y:cmp(x[k].value,y[k].value))
            s.sort(cmp=lambda x,y:cmp(x[k].partnumber,y[k].partnumber))
            s.sort(cmp=lambda x,y:cmp(x[k].manufacturer,y[k].manufacturer))
            return s

        def fix_dni(part_list,k):
            for p in part_list:
                if p[k].value.upper()=='DNI':
                    p[k].manufacturer=''
                    p[k].partnumber=''

        eco = self.calculateECO(newBom)

        remove_list = filter(lambda x:x[0]=='remove',eco)
        add_list = filter(lambda x:x[0]=='add',eco)
        change_list = filter(lambda x:x[0]=='change',eco)
        lst = ["action,ref,old manufacturer,old part number,old value,,new manufacturer,new part number,new value".split(',')]

        remove_list = sort_part_list(remove_list,2)
        for change,ref,oldpart in remove_list:
            s =  ['remove', ref,oldpart.manufacturer,oldpart.partnumber,oldpart.value]
            lst.append(s)

        change_list = sort_part_list(change_list,3)
        for change,ref,oldpart,newpart in change_list:
            if oldpart.partnumber==newpart.partnumber:
                if not compare_mfg(oldpart.manufacturer,newpart.manufacturer):
                    s = ["mfgchg",
                         ref,
                         oldpart.manufacturer,oldpart.partnumber,oldpart.value,
                         "now",
                         newpart.manufacturer,newpart.partnumber,newpart.value]
                    lst.append(s)
                else:
                    if valuechg:
                        s = ["valuechg",
                             ref,
                             oldpart.manufacturer,oldpart.partnumber,oldpart.value,
                             "now",
                             newpart.manufacturer,newpart.partnumber,newpart.value]
                        lst.append(s)
            else:
                s = ["pnchg",
                     ref,
                     oldpart.manufacturer,oldpart.partnumber,oldpart.value,
                     "now",
                     newpart.manufacturer,newpart.partnumber,newpart.value]
                lst.append(s)

        add_list = sort_part_list(add_list,2)
        
        for add,ref,newpart in add_list:
            s = ["add",
                 ref,
                 "","","","now",
                 newpart.manufacturer,newpart.partnumber,newpart.value]
            lst.append(s)
            #print(s)
        return lst


if __name__=='__main__':

    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("--compare", dest="compare", 
                       default=False, action="store_true",
                       help="Generate text-based comparison of two BOMs")

    parser.add_option("--eco", dest="eco", default=None,
                      help="Store ECO to CSV format file")
    
    (options,args) = parser.parse_args()


    if options.compare or options.eco:
        if len(args)!=2:
            print("Must specify OLD and NEW BOMs")
        else:
            old = BOM(open(args[0]))
            new = BOM(open(args[1]))

            if options.compare:
                old.compare(new)
            if options.eco:
                old.showECO(new,outfile=open(options.eco,'wb'))
                
                               
