#!/usr/bin/python
############################################################################
############################################################################
"""
##  modgen - Module Generator Program for Kicad PCBnew V0.5
## 
##  Designed by
##         A.D.H.A.R Labs Research,Bharat(India)
##            Abhijit Bose( info@adharlabs.in )
##                http://ahdarlabs.in
##
## License:
## Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported
## CC BY-NC-SA 3.0 http://creativecommons.org/licenses/by-nc-sa/3.0/
## http://creativecommons.org/licenses/by-nc-sa/3.0/legalcode
"""
##
## Version History:
## version 0.0 - Initial Release (2012-03-16)
##          -- Support for Single Inline Connectors
## version 0.1 - (2012-03-18)
##          -- Updated with mm to Mil Converter tool
##          -- Corrected the Error in Locking Silk screen
## version 0.2 - (2012-03-23)
##          -- Added Mil to mm and viz. Option
##          -- Added Check for Oblong pads
##          -- GUI Reorganized
##          -- Added Auto Name Generation
## version 0.3 - (2012-03-24)
##          -- Corrected SMD Pad Mask
##          -- Added DIP & CONN-Dual Package Support
##          -- Added Quad Package support with variable pin structure
##          -- Logical GUI Re-arrangements and improvements
##          -- Custom value Population using Package type selection
##          -- Automatic Picture Dispay for Package & Configurations
## version 0.4 - (2012-04-27)
##          -- Automatic unit Conversion support 
##          -- Units support for MM
##          -- Automatic Name, Description and Keywords Generation
##              for SIP,DIP,CONN-Dual packages with support
##              for MM and Mils nameing
## version 3.0.1 - (2012-11-30)
##          -- Upgraded to python 3
## version 0.5 - (2012-11-21)
##          -- Finxed minor bug in Name genration of CONN2X
##          
## TODO:
## - Automatic Name Generation
## - Add Lib Gen Capability
##
############################################################################
############################################################################
#IMPORTS>
############################################################################
import sys
#validation for Old to New Python
if sys.version_info < (3, 0):
  #{
  from Tkinter import *
  import xml.dom.minidom,re,os,ttk,tkMessageBox
  #}
else:
  #{
  import tkinter as Tkinter
  import tkinter.ttk as ttk
  from tkinter import *
  import xml.dom.minidom,re,os
  import tkinter.messagebox as tkMessageBox
  #}
############################################################################
#EXPORT>
############################################################################
__author__ = "Abhijit Bose(info@adharlabs.in)"
__author_email__="info@adharlabs.in"
__version__ = "0.5"
############################################################################    
#DEBUG> Print Additional Debug Messages
#  if needed make _debug_message = 1
############################################################################
_debug_message = 1
############################################################################
#FORMAT>Lib
############################################################################
template_pcb = """PCBNEW-LibModule-V1  07-02-2012 08:54:12
# encoding utf-8
Units mm
$INDEX
%(modname)s
$EndINDEX
#
# %(modname)s PACK[%(package)s] 
#
$MODULE %(modname)s
Po 0 0 0 15 4F309929 00000000 ~~
Li %(modname)s
Cd %(description)s
Kw %(keywords)s
Sc 00000000
AR %(modname)s
Op 0 0 0
T0 0 %(modref_y)s 1.5 1.5 0 0.3 N V 21 "%(refname)s"
T1 0 -1.25 0.125 0.125 0 0.025 N I 21 "VAL**"
%(drawing)s
%(pads)s
$EndMODULE  %(modname)s
$EndLIBRARY
#
# End Module
"""
template_pad="""
$PAD
Sh %(shape)s
Dr %(drill)s
At %(padtype)s N %(layermask)s
Ne 0 ""
Po %(pinx)s %(piny)s
$EndPAD"""
template_lib = """EESchema-LIBRARY Version 2.3  Date: 6/1/2012-05:30AM IST
#encoding utf-8
Units mm
#
# %(compname)s
#
DEF %(compname)s %(refname)s 0 0.1 Y Y 0.0025 F N
F0 "%(refname)s" 0 %(refname_y)s 0.125 H V C C N N
F1 "%(compname)s" 0 %(compname_y)s 0.125 H V C C N N
DRAW
%(box)s
%(pins)s
ENDDRAW
ENDDEF
#
# End Library
"""
template_dcm = """EESchema-DOCLIB  Version 2.0  Date: 6/1/2012-05:30AM IST
#
$CMP %(compname)s
%(dk)s
$ENDCMP
#
# End Doc Library
"""
############################################################################
#FORMAT FUNCTIONS>
############################################################################
def PinDescriptions(comp):
  "Read in the pin descriptions as a list"
  el = xmlcomp.getElementsByTagName("module")[0]
  xbits=[i.data for i in el.childNodes if i.nodeType==el.TEXT_NODE]
  
  # Split into lines
  bits = "".join(xbits).split("\n")
  #Remove white space
  bits = [ i.strip() for i in bits ]
  #Remove empty strings
  bits = [ i for i in bits if i!="" ]
  #Get the Pin names & Modes
  bits = [ i.split(',') for i in bits]
  return bits
############################################################################
def PinGen(numb):
  "Generate Pin Numbers if No pin Description is available using PIN"
  bits = []
  for i in range(1,numb+1):
    bits.append(str(i))
  #print bits
  return bits
############################################################################
def MetaData(comp):
  "Extract the component description parameters (common to all pins)"
  el = comp.getElementsByTagName("module")[0]
  d = {}
  for name, value in list(el.attributes.items()) :
    d[name] = value
  return d
############################################################################
def Generate_Rectangle(starting_x,starting_y,ending_x,ending_y,line_thickness):
  "Returns a string containing a rectangle. (Used for making package borders)"
  rectangle  =   "DS %+f %+f %+f %+f %+f 21"%(starting_x,starting_y,ending_x,starting_y,line_thickness)
  rectangle += "\nDS %+f %+f %+f %+f %+f 21"%(starting_x,starting_y,starting_x,ending_y,line_thickness)
  rectangle += "\nDS %+f %+f %+f %+f %+f 21"%(starting_x,ending_y,ending_x,ending_y,line_thickness)
  rectangle += "\nDS %+f %+f %+f %+f %+f 21"%(ending_x,starting_y,ending_x,ending_y,line_thickness)
  return rectangle
############################################################################
def MakePads_SIP(pins,meta):
  """To Make the Pads and draw outline for SIP Connector"""

  drawing_line_thickness = 0.3
  #This determines the package size as offset from pin 1
  outline_offset = 1.25

  pin_str = ""
  x = 0
  y = 0
  pin = {}
  pitch = float(meta["pitch"])
  locking = 0
  for p in pins:
    if(meta["locking"]!=None):
      if(locking==0):
        locking=1
        pin["piny"]="%+f"%(y+(float(meta["locking"])))
      else:
        locking=0
        pin["piny"]="%+f"%(y-(float(meta["locking"])))
    else:
      pin["piny"]="%+f"%(y)
    pin["pinx"]="%+f"%(x)
    x = x + pitch
    pin["padtype"]=meta["padtype"]
    pin["layermask"]=meta["padlayermask"]
    pin["drill"]="%+f 0 0"%(float(meta["paddrill"]))
    if(x==pitch and meta["firstpadsquare"]!= None):
      pin["shape"]="\"%s\" %s %+f %+f 0 0 0"%(p[0],"R",\
          float(meta["padx"]),float(meta["pady"]))
    else:
      pin["shape"]="\"%s\" %s %+f %+f 0 0 0"%(p[0],meta["padshape"],\
          float(meta["padx"]),float(meta["pady"]))
    pin_str += template_pad%pin #Add the Pad
  # Make Drawing  
  buf = (max(float(meta["padx"]),float(meta["pady"]))+outline_offset)
  X = x - pitch + buf
  mx = buf/-2
  if(meta["locking"]!=None):#Add some margin for Locking
    buf = buf + (float(meta["locking"])*2)
  Y = buf #Increase Y Only  
  my = buf/-2
  meta["drawing"]=Generate_Rectangle(mx,my,mx+X,my+Y,drawing_line_thickness)
  meta["modref_y"]="-2.5"
  return pin_str
############################################################################
def MakePads_DIP(pins,meta):
  """To Make the Pads and draw outline for DIP Package"""
  pin_str = ""
  x = 0
  y = 0
  pin = {}
  pitch = float(meta["pitch"]) * 10
  #Set First Half of the Pins
  for i in range(0,int(len(pins)/2)):
    pin["piny"]="%d"%(y)
    pin["pinx"]="%d"%(x)
    y = y + pitch
    pin["padtype"]=meta["padtype"]
    pin["layermask"]=meta["padlayermask"]
    pin["drill"]="%d 0 0"%(int(float(meta["paddrill"])*10))
    if(x==pitch and meta["firstpadsquare"]!= None):
      pin["shape"]="\"%s\" %s %d %d 0 0 0"%(pins[i],"R",\
          float(meta["padx"])*10,float(meta["pady"])*10)
    else:
      pin["shape"]="\"%s\" %s %d %d 0 0 0"%(pins[i],meta["padshape"],\
          float(meta["padx"])*10,float(meta["pady"])*10)
    pin_str += template_pad%pin #Add the Pad
  #Increment the Next Row
  x = float(meta["rowx"])*10
  y = y - pitch
  #Set Second Half of the Pins
  for i in range(int(len(pins)/2),len(pins)):
    pin["piny"]="%d"%(y)
    pin["pinx"]="%d"%(x)
    y = y - pitch
    pin["padtype"]=meta["padtype"]
    pin["layermask"]=meta["padlayermask"]
    pin["drill"]="%d 0 0"%(int(float(meta["paddrill"])*10))
    pin["shape"]="\"%s\" %s %d %d 0 0 0"%(pins[i],meta["padshape"],\
          float(meta["padx"])*10,float(meta["pady"])*10)
    pin_str += template_pad%pin #Add the Pad
  # Make Drawing  
  bufx = (float(meta["padx"])+100+float(meta["rowx"]))*10
  bufy = ((float(meta["pitch"])*(len(pins)-2)/2.0)\
          +100+float(meta["pady"]))*10
  X = bufx
  mx = ((float(meta["padx"])/-2.0)-50)*10
  Y = bufy
  my = ((float(meta["pady"])/-2.0)-50)*10
  drawing  = "DS %d %d %d %d 120 21"%(mx,my,mx+X,my)
  drawing += "\nDS %d %d %d %d 120 21"%(mx,my,mx,Y+my)
  drawing += "\nDS %d %d %d %d 120 21"%(mx,Y+my,mx+X,Y+my)
  drawing += "\nDS %d %d %d %d 120 21"%(mx+X,my,mx+X,Y+my)
  drawing += "\nDC %d %d %d %d 120 21"%(mx-500,0,mx-200,0)
  meta["drawing"]=drawing
  meta["modref_y"]="-1500"
  return pin_str
############################################################################
def MakePads_CONN_Dual(pins,meta):
  """ To Make the Pads and draw outline for Dual row Connector """

  drawing_line_thickness = 0.3
  #This determines the package size as offset from pin 1
  outline_offset = 1.25
  #How far to the left of the package outline the circle's center is
  circle_center_offset = 1.25
  circle_radius = 0.75

  pin_str = ""
  x = 0.0
  y = 0.0
  pin = {}
  pitch = float(meta["pitch"])
  for i in range(0,len(pins)):
    pin["piny"]="%+f"%(y)
    pin["pinx"]="%+f"%(x)
    if (i&1)==0:#Next Even Pin
      x = float(meta["rowx"])
    else:#Next Odd Pin
      x = 0
      y = y + pitch
    pin["padtype"]=meta["padtype"]
    pin["layermask"]=meta["padlayermask"]
    pin["drill"]="%+f 0 0"%(float(meta["paddrill"]))
    if(i == 0 and meta["firstpadsquare"]!= None):
      pin["shape"]="\"%s\" %s %+f %+f 0 0 0"%(pins[i],"R",\
          float(meta["padx"]),float(meta["pady"]))
    else:
      pin["shape"]="\"%s\" %s %+f %+f 0 0 0"%(pins[i],meta["padshape"],\
          float(meta["padx"]),float(meta["pady"]))
    pin_str += template_pad%pin #Add the Pad
  # Make Drawing  
  X  = (float(meta["padx"])+(2*outline_offset)+float(meta["rowx"]))
  Y  = ((float(meta["pitch"])*(len(pins)-2)/2.0)+(2*outline_offset)+float(meta["pady"]))
  mx = ((float(meta["padx"])/-2.0)-outline_offset)
  my = ((float(meta["pady"])/-2.0)-outline_offset)
  drawing = Generate_Rectangle(mx,my,mx+X,my+Y,drawing_line_thickness)
  drawing += "\nDC %+f %+f %+f %+f %+f 21"%(mx-circle_center_offset,0,mx-circle_center_offset-circle_radius,0,drawing_line_thickness)
  meta["drawing"]=drawing
  meta["modref_y"]="-3.8"
  return pin_str
############################################################################
def MakePads_QUAD(pins,meta):
  """To Make the Pads and draw outline for Quad Package"""
  pin_str = ""  
  pitch = float(meta["pitch"]) * 10  
  pin = {}  
  #Make the Left side
  x = (float(meta["rowx"])/-2.0)*10 
  y = (pitch*(int(meta["PIN_N_HORIZ"]))/-2.0)+(pitch/2.0)
  b = 0
  n = int(meta["PIN_N_HORIZ"])
  for i in range(b,n):
    pin["piny"]="%d"%(y)
    pin["pinx"]="%d"%(x)
    y = y + pitch
    pin["padtype"]=meta["padtype"]
    pin["layermask"]=meta["padlayermask"]
    pin["drill"]="%d 0 0"%(int(float(meta["paddrill"])*10))
    if(i == 0 and meta["firstpadsquare"]!= None):
      pin["shape"]="\"%s\" %s %d %d 0 0 0"%(pins[i],"R",\
          float(meta["padx"])*10,float(meta["pady"])*10)
    else:
      pin["shape"]="\"%s\" %s %d %d 0 0 0"%(pins[i],meta["padshape"],\
          float(meta["padx"])*10,float(meta["pady"])*10)
    pin_str += template_pad%pin #Add the Pad
  #Make the Bottom side
  x = ((pitch*(int(meta["PIN_N_VERT"])))/-2.0)+(pitch/2.0)
  y = (float(meta["rowy"])/2.0)*10
  b = int(meta["PIN_N_HORIZ"])
  n = int(meta["PIN_N_HORIZ"])+int(meta["PIN_N_VERT"])
  for i in range(b,n):
    pin["piny"]="%d"%(y)
    pin["pinx"]="%d"%(x)
    x = x + pitch
    pin["padtype"]=meta["padtype"]
    pin["layermask"]=meta["padlayermask"]
    pin["drill"]="%d 0 0"%(int(float(meta["paddrill"])*10))
    pin["shape"]="\"%s\" %s %d %d 0 0 0"%(pins[i],meta["padshape"],\
        float(meta["pady"])*10,float(meta["padx"])*10)
    pin_str += template_pad%pin #Add the Pad
  #Make the Right side
  x = (float(meta["rowx"])/2.0)*10 
  y = (pitch*(int(meta["PIN_N_HORIZ"]))/2.0)-(pitch/2.0)
  b = int(meta["PIN_N_HORIZ"])+int(meta["PIN_N_VERT"])
  n = (int(meta["PIN_N_HORIZ"])*2)+int(meta["PIN_N_VERT"])
  for i in range(b,n):
    pin["piny"]="%d"%(y)
    pin["pinx"]="%d"%(x)
    y = y - pitch
    pin["padtype"]=meta["padtype"]
    pin["layermask"]=meta["padlayermask"]
    pin["drill"]="%d 0 0"%(int(float(meta["paddrill"])*10))
    pin["shape"]="\"%s\" %s %d %d 0 0 0"%(pins[i],meta["padshape"],\
          float(meta["padx"])*10,float(meta["pady"])*10)
    pin_str += template_pad%pin #Add the Pad
  #Make the Top side
  x = (pitch*(int(meta["PIN_N_VERT"]))/2.0)-(pitch/2.0)
  y = (float(meta["rowy"])/-2.0)*10
  b = (int(meta["PIN_N_HORIZ"])*2)+int(meta["PIN_N_VERT"])
  n = int(meta["PIN_N"])
  for i in range(b,n):
    pin["piny"]="%d"%(y)
    pin["pinx"]="%d"%(x)
    x = x - pitch
    pin["padtype"]=meta["padtype"]
    pin["layermask"]=meta["padlayermask"]
    pin["drill"]="%d 0 0"%(int(float(meta["paddrill"])*10))
    pin["shape"]="\"%s\" %s %d %d 0 0 0"%(pins[i],meta["padshape"],\
        float(meta["pady"])*10,float(meta["padx"])*10)
    pin_str += template_pad%pin #Add the Pad
  # Make Drawing
  mx = ((float(meta["rowx"])/-2.0)-(float(meta["padx"])/2.0)-50)*10
  my = ((float(meta["rowy"])/-2.0)-(float(meta["padx"])/2.0)-50)*10
  X = -mx  
  Y = -my
  meta["modref_y"] = "%d"%(my - 500)
  drawing  = "DS %d %d %d %d 120 21"%(mx+500,my,X,my)
  drawing += "\nDS %d %d %d %d 120 21"%(mx,my+500,mx,Y)
  drawing += "\nDS %d %d %d %d 120 21"%(mx,Y,X,Y)
  drawing += "\nDS %d %d %d %d 120 21"%(X,my,X,Y)
  drawing += "\nDS %d %d %d %d 120 21"%(mx,my+500,mx+500,my)
  my = (pitch*(int(meta["PIN_N_HORIZ"]))/-2.0)+(pitch/2.0)
  drawing += "\nDC %d %d %d %d 120 21"%(mx-800,my,mx-600,my+200)
  meta["drawing"]=drawing
  return pin_str
############################################################################  
def MakePads(pins,meta):
  """Convert the Pins into a string of Pad data and add Drawing"""
  if meta["package"]=='SIP':
    return MakePads_SIP(pins,meta)
  elif meta["package"]=='DIP':
    return MakePads_DIP(pins,meta)
  elif meta["package"]=='CONN-Dual':
    return MakePads_CONN_Dual(pins,meta)
  elif meta["package"]=='QUAD':
    return MakePads_QUAD(pins,meta)
  print("Error: Un Supported Package")
  exit(0)
############################################################################
#GUI FUNCTIONS>
############################################################################
def mmtomil(mm):
  ''' Function to convert the mm into mils even when its a string
     and return accordingly '''
  global er
  s = 0
  if (type(mm) == type(" ")):
    try:
      mm = float(mm)
      s = 1
    except:
      er = "Unit Conversion Fault"
      return 0
  mil = mm * 1000/25.4
  if s==1:
    mil = "%f"%mil
  er = "ok"
  return mil
############################################################################
def miltomm(mil):
  ''' Function to convert the mils into mm even when its a string
     and return accordingly '''
  global er
  s = 0
  if (type(mil) == type(" ")):
    try:
      mil = float(mil)
      s = 1
    except:
      er = "Unit Conversion Fault"
      return 0
  mm = mil * 25.4/1000
  if s==1:
    mm = "%f"%mm
  er = "ok"
  return mm
############################################################################
def Validate():
  """To Validate the GUI Inputs"""
  global er
  er = 1
  # Check Pitch
  try:
    k = float(pitch.get())*1.0
    er = "ok"
    if (k<=0 or k>=400) and units.get()=="mils":
      tkMessageBox.showerror("Error","Invalid Pitch Value")        
      er = "pitch"
      pitch.set("100")
      return 1
    elif (k<=0 or k>=10) and units.get()=="mm":
      tkMessageBox.showerror("Error","Invalid Pitch Value")        
      er = "pitch"
      pitch.set("2.54")
      return 1
  except:    
    tkMessageBox.showerror("Error","Invalid Pitch Value")        
    er = "pitch"
    if units.get()=="mm":
      pitch.set("2.54")
    else:
      pitch.set("100")
    return 1
  # Check Padx
  try:
    k = float(padx.get())*1.0
    er = "ok"
    if (k<=0):
      tkMessageBox.showerror("Error","Invalid Pad X Value")    
      er = "padx"
      if units.get()=="mils":
        padx.set("70")
      else:
        padx.set("1.778")
      return 1
  except:    
    tkMessageBox.showerror("Error","Invalid Pad X Value") 
    er = "padx"
    if units.get()=="mils":
      padx.set("70")
    else:
      padx.set("1.778")
    return 1
  # Check Pady
  try:
    k = float(pady.get())*1.0
    er = "ok"
    if(k<=0):
      tkMessageBox.showerror("Error","Invalid Pad Y Value")      
      er = "pady"
      if units.get()=="mils":
        pady.set("70")
      else:
        pady.set("1.778")
      return 1
  except:    
    tkMessageBox.showerror("Error","Invalid Pad Y Value")      
    er = "pady"
    if units.get()=="mils":
      pady.set("70")
    else:
      pady.set("1.778")
    return 1
  # Check Pad Drill
  try:
    k = float(paddrill.get())*1.0
    er = "ok"
    if(k<=10 or k>250) and padtype.get()=='STD'and units.get()=="mils":
      tkMessageBox.showerror("Error","Invalid Pad Drill Value") 
      er = "paddrill"
      paddrill.set("35")
      return 1
    elif(k<=0.254 or k>6.1) and padtype.get()=='STD'and units.get()=="mm":
      tkMessageBox.showerror("Error","Invalid Pad Drill Value")      
      er = "paddrill"
      paddrill.set(".889")
      return 1
    #elif padtype.get()=='SMD':#Allow Even Drils if needed
    #  paddrill.set("0")
  except:    
    tkMessageBox.showerror("Error","Invalid Pad Drill Value") 
    er = "paddrill"
    if units.get() == "mils":
      paddrill.set("35")
    else:
      paddrill.set(".889")
    return 1
  # Check Pin N
  try:
    k = int(PIN_N.get())*1
    er = "ok"
    if(k<=1):
      tkMessageBox.showerror("Error","Invalid Number of Pins")  
      er = "PIN_N"
      PIN_N.set("8")
      return 1
    if (k%2)!=0 and (package.get() in ['DIP','CONN-Dual']):
      tkMessageBox.showerror("Error","Invalid Number of Pins")    
      er = "PIN_N"
      PIN_N.set("8")
      return 1
  except:    
    tkMessageBox.showerror("Error","Invalid Number of Pins")    
    er = "PIN_N"
    PIN_N.set("8")
    return 1
  # Check Row X
  try:
    k = float(rowx.get())*1
    er = "ok"
    if (k<=0) and (package.get() in ['DIP','CONN-Dual']):
      tkMessageBox.showerror("Error","Invalid Row X Spacing")    
      er = "RowX"
      if units.get() == "mils":
        rowx.set("10")
      else:
        rowx.set("0.254")
      return 1
  except:    
    tkMessageBox.showerror("Error","Invalid Row X Spacing")  
    er = "RowX"
    return 1
  # Check Row Y
  try:
    k = float(rowy.get())*1
    er = "ok"
    if (k<=0) and (package.get() in ['QUAD']):
      tkMessageBox.showerror("Error","Invalid Row Y Spacing") 
      er = "RowY"
      if units.get() == "mils":
        rowy.set("10")
      else:
        rowy.set("0.254")
      return 1
  except:    
    tkMessageBox.showerror("Error","Invalid Row Y Spacing")  
    er = "RowY"
    return 1
  # Check PIN_N_HORIZ
  try:
    k = int(PIN_N_HORIZ.get())*1
    er = "ok"
    if (k<=0) and (package.get() in ['QUAD']):
      tkMessageBox.showerror("Error","Invalid Number of Pins Horizontally")   
      er = "PIN_N_HORIZ"
      PIN_N_HORIZ.set("%d"%(int(PIN_N.get())/4))
      return 1
  except:    
    tkMessageBox.showerror("Error","Invalid Number of Pins Horizontally") 
    er = "PIN_N_HORIZ"
    return 1
  #Check The Description
  if(len(description.get())==0):
    description.set(modname.get())
  #Check The Keywords
  if(len(keywords.get())==0):
    keywords.set(modname.get())  
  #Check the Oblong Selection PadY>Padx
  if(float(padx.get())==float(pady.get())) and padshape.get()=='O':
    tkMessageBox.showerror("Error","Incorrect Pad Dimensions for Oblong pads")
    er = "Oblong Pad Shape"
    return 1
  #Check the Circle Selection PadY=Padx
  if(float(padx.get())!=float(pady.get())) and padshape.get()=='C':
    tkMessageBox.showerror("Error",\
      "Incorrect Pad Dimensions for Circular pads")
    er = "Circular Pad Shape"
    return 1
  #At the End Return
  return 1
############################################################################
def autouintadjust():
  ''' Automatically adjust the units as per selection '''
  try:
    if units.get() == "mm":#Preivious was Mils    
      pitch.set(miltomm(pitch.get()))
      padx.set(miltomm(padx.get()))
      pady.set(miltomm(pady.get()))
      paddrill.set(miltomm(paddrill.get()))
      rowx.set(miltomm(rowx.get()))
      rowy.set(miltomm(rowy.get()))
    if units.get() == "mils":#Preivious was mm
      pitch.set(mmtomil(pitch.get()))
      padx.set(mmtomil(padx.get()))
      pady.set(mmtomil(pady.get()))
      paddrill.set(mmtomil(paddrill.get()))
      rowx.set(mmtomil(rowx.get()))
      rowy.set(mmtomil(rowy.get()))
  except:
    print('Error in Unit Conversion')
    tkMessageBox.showerror("Error","Error in Unit Conversion")
############################################################################
def packed():
  """To Pack the GUI inputs to the XML form"""
  #Convert to Mils as all processing is in mils
  #Not anymore it isn't
  #if units.get() == "mm":
  #  units.set("mils")
  #  autouintadjust()
  #Run Validation Check
  Validate()  
  if er != "ok":    
    print("Error In " + er)
    return 0
  print("Module Name: " + modname.get())
  meta["modname"] = modname.get()
  print("Reference Designator: " + refdes.get())
  meta["refname"] = refdes.get()
  print("Package: " + package.get())
  meta["package"] = package.get()
  print("Pitch: " + pitch.get())
  meta["pitch"] = pitch.get()
  print("Pad x Dimension: " + padx.get())
  meta["padx"] = padx.get()
  print("Pad y Dimension: " + pady.get())
  meta["pady"] = pady.get()
  print("Pad Drill Diameter: " + paddrill.get())
  meta["paddrill"] = paddrill.get()
  print("Pad Shape: "+ padshape.get())
  meta["padshape"] = padshape.get()
  print("First Pad Square: " + ("True" if firstpinsquare.get() else "False"))
  meta["firstpadsquare"] = 1 if firstpinsquare.get() else None
  print("Self Locking Pattern: " + ("True" if locking.get() else "False"))
  meta["locking"] = "0.125" if locking.get() else None
  print("Pad Type: " + padtype.get())
  meta["padtype"] = padtype.get()
  if padtype.get() == 'STD':
    meta["padlayermask"]='00E0FFFF' #normally for STD 
  else:
    meta["padlayermask"]='00888000' #notmally for SMD
  print("Number of Pins: " + PIN_N.get())
  meta["PIN_N"] = PIN_N.get()
  pins = PinGen(int(meta["PIN_N"]))
  print("Description for Module: " + description.get())
  meta["description"] = description.get()
  print("Keywords for Module: " + keywords.get())
  meta["keywords"] = keywords.get()
  if meta["package"] in ['DIP','CONN-Dual','QUAD']:
    print("Pin Row Spacing X:" + rowx.get())
    meta["rowx"] = rowx.get()
  else:
    meta["rowx"] = None
  if meta["package"] =='QUAD':
    print("Pin Row Spacing Y:" + rowy.get())
    meta["rowy"] = rowy.get()
    print("Number of Pins Horizontally: " + PIN_N_HORIZ.get())
    meta["PIN_N_HORIZ"] = PIN_N_HORIZ.get()
    meta["PIN_N_VERT"] = "%d"%(\
      (int(PIN_N.get())-(int(PIN_N_HORIZ.get())*2))/2)
    print("Number of Pins Vertically: " + meta["PIN_N_VERT"])
  else:
    meta["rowy"] = None
    meta["PIN_N_HORIZ"] = None
    meta["PIN_N_VERT"] = None
  #Generate the Pad description
  meta["pads"]=MakePads(pins,meta)
  print(template_pcb%meta)
  name = meta["modname"]
  if(locking.get()) and package.get() == 'SIP':
    name = name+"_LOCK"
  name = name+".emp"
  ans = tkMessageBox.askokcancel("File Wite",\
        "Do you want to wite "+name+" for the Module?")
  if(ans):
    fl = open(name,"w")
    fl.write(template_pcb%meta)
    fl.close()
    tkMessageBox.showinfo("Module Generator",\
      "Module "+meta["modname"]+" Written Successfully!!")
    print(" Module "+name+" written successfully")
  return 1
############################################################################
def draw():
  '''Draw Pictures depending on Package and configuration'''
  canvas.delete("all")
  if package.get() == 'SIP':
    canvas.create_rectangle(40,40,160,80,width=3)
    #First Pad
    x = 55
    y = 55
    if locking.get() == False:
      xy = x,y,x+10,y+10
      if firstpinsquare.get():
        canvas.create_rectangle(xy,width=5)
      else:
        canvas.create_oval(xy,width=5)
      canvas.create_text(x+5,30,text="1",fill="red")
      #Further pads
      for i in range(0,4):
        x = x + 20
        xy = x,y,x+10,y+10
        canvas.create_oval(xy,width=5)
        canvas.create_text(x+5,30,text="%d"%(i+2),fill="red")
      #Pitch
      canvas.create_line(60,60,60,100,width=2,fill='red')
      canvas.create_line(80,60,80,100,width=2,fill='red')
      canvas.create_line(40,90,60,90,width=2,arrow=LAST,fill='blue')
      canvas.create_line(80,90,100,90,width=2,arrow=FIRST,fill='blue')
      canvas.create_text(70,110,text="Pitch",font=("Arial",10,"bold"),\
                         fill="blue")
    else: #LOcked SIP type
      l=1
      for i in range(0,5):
        l = 1 if l==0 else 0
        if l == 0:
          xy = x,y+5,x+10,y+15
        else:
          xy = x,y-5,x+10,y+5
        x = x + 20
        if i==0 and firstpinsquare.get():
          canvas.create_rectangle(xy,width=5)
        else:
          canvas.create_oval(xy,width=5)
        canvas.create_text(x-15,30,text="%d"%(i+1),fill="red")
      #Pitch
      canvas.create_line(60,65,60,100,width=2,fill='red')
      canvas.create_line(80,55,80,100,width=2,fill='red')
      canvas.create_line(40,90,60,90,width=2,arrow=LAST,fill='blue')
      canvas.create_line(80,90,100,90,width=2,arrow=FIRST,fill='blue')
      canvas.create_text(70,110,text="Pitch",font=("Arial",10,"bold"),\
                         fill="blue")
      #Lock
      canvas.create_line(20,65,60,65,width=2,fill='red')
      canvas.create_line(20,55,80,55,width=2,fill='red')
      canvas.create_line(30,35,30,55,width=2,arrow=LAST,fill='blue')
      canvas.create_line(30,90,30,65,width=2,arrow=LAST,fill='blue')
      canvas.create_text(30,30,text="Lock",font=("Arial",10,"bold"),\
                         fill="blue")
  elif package.get() == 'DIP':
    canvas.create_rectangle(60,30,160,100,width=3)
    xy = 40,40,50,50
    canvas.create_oval(xy,width=3)
    xy = 100,20,120,40
    canvas.create_arc(xy,start=180,extent=180,width=3)
    #First Set
    x = 70
    y = 40
    for i in range(0,3):
      xy = x,y,x+30,y+10
      y = y + 20
      canvas.create_oval(xy,width=5)
      canvas.create_text(x-50,y-20,text="%d"%(i+1),fill="red")
    #Second Set
    x = 120
    y = 40
    for i in range(0,3):
      xy = x,y,x+30,y+10
      y = y + 20
      canvas.create_oval(xy,width=5)
      canvas.create_text(x+50,y-20,text="%d"%(6-i),fill="red")
    #Pitch
    canvas.create_line(30,65,90,65,width=2,fill='red')
    canvas.create_line(30,85,90,85,width=2,fill='red')
    canvas.create_line(30,50,30,65,width=2,arrow=LAST,fill='blue')
    canvas.create_line(30,85,30,100,width=2,arrow=FIRST,fill='blue')
    canvas.create_text(40,75,text="Pitch",font=("Arial",10,"bold"),\
                       fill="blue")
    #Row X
    canvas.create_line(85,20,85,45,width=2,fill='red')
    canvas.create_line(135,20,135,45,width=2,fill='red')
    canvas.create_line(85,20,135,20,width=2,arrow=BOTH,fill='blue')
    canvas.create_text(110,10,text="Row Spacing X",font=("Arial",10,"bold"),\
                       fill="blue")

  elif package.get() == 'CONN-Dual':
    canvas.create_rectangle(60,30,110,100,width=3)
    xy = 40,40,50,50
    canvas.create_oval(xy,width=3)
    #First Set
    x = 70
    y = 40
    k = 1
    for i in range(0,3):
      xy = x,y,x+10,y+10
      y = y + 20
      if i==0 and firstpinsquare.get():
        canvas.create_rectangle(xy,width=5)
      else:
        canvas.create_oval(xy,width=5)
      canvas.create_text(x-50,y-20,text="%d"%(k),fill="red")
      k = k + 2
    #Second Set
    x = 90
    y = 40
    k = 2
    for i in range(0,3):
      xy = x,y,x+10,y+10
      y = y + 20
      canvas.create_oval(xy,width=5)
      canvas.create_text(x+30,y-20,text="%d"%(k),fill="red")
      k = k + 2
    #Pitch
    canvas.create_line(30,65,75,65,width=2,fill='red')
    canvas.create_line(30,85,75,85,width=2,fill='red')
    canvas.create_line(30,50,30,65,width=2,arrow=LAST,fill='blue')
    canvas.create_line(30,85,30,100,width=2,arrow=FIRST,fill='blue')
    canvas.create_text(40,75,text="Pitch",font=("Arial",10,"bold"),\
                       fill="blue")
    #Row X
    canvas.create_line(75,20,75,45,width=2,fill='red')
    canvas.create_line(95,20,95,45,width=2,fill='red')
    canvas.create_line(40,20,75,20,width=2,arrow=LAST,fill='blue')
    canvas.create_line(95,20,130,20,width=2,arrow=FIRST,fill='blue')
    canvas.create_text(85,10,text="Row Spacing X",font=("Arial",10,"bold"),\
                       fill="blue")
  elif package.get() == 'QUAD':
    x = 50
    y = 40
    dx = 120
    dy = 120
    canvas.create_polygon(\
      x,y+20,x+20,y,x+dx,y,x+dx,y+dy,x,y+dy,fill="white",width=2,outline="black")
    xy = x-20,y+40,x-10,y+30
    canvas.create_oval(xy,width=2)
    #Left
    ox = x + 10
    oy = y + 35
    for i in range(1,5):
      xy = ox,oy,ox+20,oy+5
      canvas.create_rectangle(xy,fill="black")
      canvas.create_text(ox-50,oy+5,text="%d"%(i),fill="red")
      oy = oy + 15
    #Bottom
    ox = x + 35
    oy = y + + dy - 10
    for i in range(5,9):
      xy = ox,oy,ox+5,oy-20
      canvas.create_rectangle(xy,fill="black")
      canvas.create_text(ox+5,oy+15,text="%d"%(i),fill="red")
      ox = ox + 15
    #Right
    ox = x + dx - 10
    oy = y + dy - 35
    for i in range(9,13):
      xy = ox,oy,ox-20,oy-5
      canvas.create_rectangle(xy,fill="black")
      canvas.create_text(ox+30,oy-5,text="%d"%(i),fill="red")
      oy = oy - 15
    #Top
    ox = x + dx - 35
    oy = y + 30
    for i in range(13,17):
      xy = ox,oy,ox-5,oy-20
      canvas.create_rectangle(xy,fill="black")
      canvas.create_text(ox-5,oy-50,text="%d"%(i),fill="red")
      ox = ox - 15
    #Pitch
    canvas.create_line(x+20,y+52,x+50,y+52,fill='red')
    canvas.create_line(x+20,y+68,x+50,y+68,fill='red')
    canvas.create_line(x+50,y+40,x+50,y+52,arrow=LAST,fill='blue')
    canvas.create_line(x+50,y+68,x+50,y+80,arrow=FIRST,fill='blue')
    canvas.create_text(x+60,y+62,text="Pitch",fill="blue")
    #Row X
    canvas.create_line(x+20,y+dy-36,x+20,y+dy+30,fill='red')
    canvas.create_line(x+dx-20,y+dy-36,x+dx-20,y+dy+30,fill='red')
    canvas.create_line(x+20,y+dy+30,x+dx-20,y+dy+30,arrow=BOTH,fill='blue')
    canvas.create_text(x+60,y+dy+20,text="Row Spacing X",fill="blue")
    #Row Y
    canvas.create_line(x-30,y+20,x+35,y+20,fill='red')
    canvas.create_line(x-30,y+dy-20,x+35,y+dy-20,fill='red')
    canvas.create_line(x-25,y+20,x-25,y+dy-20,arrow=BOTH,fill='blue')
    canvas.create_text(x-25,y+dy-10,text="Row",fill="blue")
    canvas.create_text(x-25,y+dy,text="Spacing",fill="blue")
    canvas.create_text(x-25,y+dy+10,text="Y",fill="blue")
    #Pin Horiz
    ox = x - 35
    oy = y + 25
    canvas.create_line(ox,oy,ox-20,oy,fill='red')
    canvas.create_line(ox,oy,ox,oy+70,fill='red')
    canvas.create_line(ox,oy+70,ox-20,oy+70,fill='red')
    canvas.create_line(ox+10,oy-35,ox,oy,arrow=LAST,fill='blue')
    canvas.create_text(ox+20,oy-55,text="No. of Pins",fill="blue")
    canvas.create_text(ox+20,oy-45,text="Horizontally",fill="blue")
    
  #Pad Generic
  if package.get() in ['SIP','DIP','CONN-Dual']:     
    xy = 100+6,140+6,140-6,180-6
    canvas.create_oval(xy,width=12)
    canvas.create_line(60,140,120,140,width=2,fill='red')
    canvas.create_line(60,180,120,180,width=2,fill='red')
    canvas.create_line(80,140,80,180,width=2,arrow=BOTH,fill='blue')
    canvas.create_text(50,160,text="Pad Y",font=("Arial",10,"bold"),\
                       fill="blue")
    canvas.create_line(100,120,100,160,width=2,fill='red')
    canvas.create_line(140,120,140,160,width=2,fill='red')
    canvas.create_line(100,130,140,130,width=2,arrow=BOTH,fill='blue')
    canvas.create_text(120,115,text="Pad X",font=("Arial",10,"bold"),\
                       fill="blue")
    canvas.create_line(110,150,130,170,width=2,arrow=BOTH,fill='red')
    canvas.create_line(130,170,150,190,width=2,fill='red')
    canvas.create_line(150,190,190,190,width=2,fill='red')
    canvas.create_text(170,175,text="Drill Dia",font=("Arial",10,"bold"),\
                       fill="blue")
  canvas.update()
############################################################################  
def package_cmb_update(event):
  """To Update Options when the Screen is Activated"""
  units.set("mils")
  description.set("")
  keywords.set("")
  if package.get() == 'SIP':
     rowx_di()
     rowy_di()
     PIN_N_HORIZ_di()
     modname.set('CONN')
     refdes.set('J')
     PIN_N.set('8')
     pitch.set('100')
     padx.set('70')
     pady.set('70')
     paddrill.set('35')
     padshape.set('C')
     firstpinsquare.set(True)
     locking.set(False)
     padtype.set('STD')     
  elif package.get() == 'DIP':
     rowx_en()     
     rowy_di()
     PIN_N_HORIZ_di()
     modname.set('DIP')
     refdes.set('U')
     PIN_N.set('8')
     pitch.set('100')
     padx.set('150')
     pady.set('60')
     paddrill.set('39.37')
     rowx.set(value="300")
     padshape.set('O')
     firstpinsquare.set(False)
     locking.set(False)
     padtype.set('STD')     
  elif package.get() == 'CONN-Dual':
     rowx_en()
     rowy_di()
     PIN_N_HORIZ_di()
     modname.set('CONN2X')
     refdes.set('J')
     PIN_N.set('16')
     pitch.set('100')
     padx.set('70')
     pady.set('70')
     paddrill.set('35')
     rowx.set(value="100")
     padshape.set('C')
     firstpinsquare.set(False)
     locking.set(False)
     padtype.set('STD')
  elif package.get() == 'QUAD':
     rowx_en()
     rowy_en()     
     PIN_N_HORIZ_en()
     modname.set('QUAD')
     refdes.set('U')
     PIN_N.set('32')
     PIN_N_HORIZ.set('4')
     pitch.set('19.74')
     padx.set('120')
     pady.set('12')
     paddrill.set('0')
     rowx.set(value="100")
     rowy.set(value="100")
     padshape.set('R')
     firstpinsquare.set(False)
     locking.set(False)
     padtype.set('SMD')
     #Default Settings only For test
     if _debug_message==1:
       modname.set('quad')
       PIN_N.set('32')
       rowx.set(value="600")
       rowy.set(value="600")
       padx.set('150')
       pady.set('20')
       pitch.set('50')
       PIN_N_HORIZ.set('4')
  draw()
############################################################################  
def autoname():
  """ To Automatically Generate the Name,Description,RefDes,
      and Keywords for the Component
  """
  if len(modname.get())!=0:
##    try:
      Validate()
      if er != "ok":    
         print("Error In " + er)
         return
      # Check for Berg Connector Single Row
      f = re.match("^(.)*(CONN)",modname.get().upper())
      g = re.match(\
          "^(.)*((?:DIP)|(?:SOIC)|(?:SSOP)|(?:TSSOP)|(?:MSOP))"\
          ,modname.get().upper())
      h = re.match("^(.)*(CONN2X)",modname.get().upper())
      
      #Get the Parameters and Format them
      if units.get()=="mm":
        pich = "%2.2f"%(float(pitch.get()))
        x = ("%2.2f"%(float(padx.get())))
        y = ("%2.2f"%(float(pady.get())))
        dril = ("%2.2f"%(float(paddrill.get())))
        rox = "%2.2f"%(float(rowx.get()))
      else:
        pich = "%d"%(float(pitch.get()))
        x = ("%d"%(float(padx.get())))
        y = ("%d"%(float(pady.get())))
        dril = ("%d"%(float(paddrill.get())))
        rox = "%d"%(float(rowx.get()))

      #Templates for Automatic Nameing
      template_desc_pcb ="""%(name)s %(pin)sPin%(rowx1)s%(fix)s %(pitch)s Pitch \
%(pad)s Pad %(drill)s %(shape)s %(type)s"""
      template_keyw_pcb ="""%(name)s%(pin)s_%(fix)s %(name)s%(pin)s_%(fix)s_\
%(pitch)s %(name)s%(pin)s%(rowx1)s_%(fix)s_%(pitch)s_%(pad)s\
_%(drill)s%(shape)s%(type)s"""
      desc = {}
      keys = {}

      #Common Generation Stub
      desc["pin"] = PIN_N.get()
      keys["pin"] = PIN_N.get()

      if padtype.get()=="STD":
        desc["fix"]="Through Hole"
        keys["fix"]="TH"
      else:
        desc["fix"]="SMD"
        keys["fix"]="SMD"
        
      desc["pitch"] = pich
      keys["pitch"] = pich

      if x != y:
        desc["pad"] = x+"X"+y        
        keys["pad"] = x+"X"+y
      else:
        desc["pad"] = x        
        keys["pad"] = x
          
      if padshape.get() =='O':
         desc["shape"] = "Oblong"
         keys["shape"] = "O"           
      elif padshape.get() =='R':
         desc["shape"] = "Rectangular"
         keys["shape"] = "R"
      else:
         desc["shape"] = "Circular"
         keys["shape"] = "C"
          
      if padtype.get()=="STD":
        desc["drill"] = dril+ " Drill"
        keys["drill"] = dril + "_"
      else:
        desc["drill"] = ""
        keys["drill"] = ""
          
      #Validate As per packages
      if f!=None and package.get()=="SIP":
        refdes.set("J")#Set the Ref
        
        desc["name"] = f.group(2)
        keys["name"] = f.group(2)
        
        desc["rowx1"] = " "
        keys["rowx1"] = ""

        if locking.get():  
          desc["type"] = "Locking"
          keys["type"] = "L"
        else:
          desc["type"] = "Normal"
          keys["type"] = "N"

        dec = template_desc_pcb % desc
        key = template_keyw_pcb % keys
                
        description.set(dec)
        keywords.set(key)
        modname.set(key.split(" ")[2])
        
      elif g!=None and package.get()=='DIP':
        refdes.set("U")#Set the Ref
        
        desc["name"] = g.group(2)
        keys["name"] = g.group(2)
        
        desc["rowx1"] = " " + rox + " Spacing "
        keys["rowx1"] = "_" + rox

        desc["type"] = ""
        keys["type"] = ""
          
        dec = template_desc_pcb % desc
        key = template_keyw_pcb % keys
        
        description.set(dec)
        keywords.set(key)
        modname.set(key.split(" ")[2])

      elif h!=None and package.get()=='CONN-Dual':
        refdes.set("J")#Set the Ref
        
        #desc["name"] = h.group(2)[:4]
        #keys["name"] = h.group(2)[:4]
        desc["name"] = h.group(2)[:6]
        keys["name"] = h.group(2)[:6]

        desc["pin"] = "%d"%(int(PIN_N.get())/2)
        keys["pin"] = "%d"%(int(PIN_N.get())/2)
        
        desc["rowx1"] = " Dual Row " + rox + " Spacing "
        keys["rowx1"] = "_" + rox

        desc["type"] = ""
        keys["type"] = ""
          
        dec = template_desc_pcb % desc
        key = template_keyw_pcb % keys
        
        description.set(dec)
        keywords.set(key)
        modname.set(key.split(" ")[2])
##    except:
##      pass
############################################################################
def Draw_MainPane(fr):
  """To Generate the Content for the Main Input Frame"""
  global modname,refdes,package,pitch,padx,pady,\
         paddrill,padshape,firstpinsquare,locking,padtype,PIN_N,\
         description,keywords,rowx,rowx_e,rowx_en,rowx_di,\
         rowy,rowy_e,rowy_en,rowy_di,units,\
         PIN_N_HORIZ,PIN_N_HORIZ_e,PIN_N_HORIZ_en,PIN_N_HORIZ_di

  Label(fr,text="Package:")\
          .grid(column=0,row=0,padx=2,pady=2,sticky=N+E)
  package=StringVar()
  pack=ttk.Combobox(fr,width=10,state="readonly",\
          values=['SIP','DIP','CONN-Dual','QUAD'],textvariable=package)
  pack.current(0)
  pack.bind("<<ComboboxSelected>>",package_cmb_update)
  pack.grid(column=1,row=0,columnspan=2,padx=2,pady=2,sticky=N+W+E)
  
  Label(fr,text="Module Name:")\
          .grid(column=0,row=1,padx=2,pady=2,sticky=N+E)
  modname=StringVar(value="Mod_Name")
  Entry(fr,textvar=modname,width=20)\
          .grid(column=1,row=1,columnspan=2,padx=2,pady=2,sticky=N+W+E)

  Label(fr,text="Reference Designator:")\
          .grid(column=0,row=2,padx=2,pady=2,sticky=N+E)
  refdes=StringVar(value="Ref_Des")
  Entry(fr,textvar=refdes,width=20)\
          .grid(column=1,row=2,columnspan=2,padx=2,pady=2,sticky=N+W+E)

  Label(fr,text="Number of Pins:")\
          .grid(column=0,row=3,padx=2,pady=2,sticky=N+E)
  PIN_N=StringVar(value="8")
  Entry(fr,textvar=PIN_N,width=20)\
          .grid(column=1,row=3,columnspan=2,padx=2,pady=2,sticky=N+W+E)
  
  Label(fr,text="Number of Pins Horizonally:")\
          .grid(column=0,row=4,padx=2,pady=2,sticky=N+E)
  PIN_N_HORIZ=StringVar(value="0")
  PIN_N_HORIZ_e = Entry(fr,textvar=PIN_N_HORIZ,width=20)
  PIN_N_HORIZ_en = lambda: \
    PIN_N_HORIZ_e.grid(column=1,row=4,columnspan=2,\
              padx=2,pady=2,sticky=N+W+E)
  PIN_N_HORIZ_di = lambda: \
    PIN_N_HORIZ_e.grid_forget()
  PIN_N_HORIZ_en()
  PIN_N_HORIZ_di()

  units_lb = ttk.Labelframe(fr,text="Units",padding=2)
  units =StringVar(value="mils")
  Radiobutton(units_lb,text="Mils",variable=units,value="mils"\
              ,command=autouintadjust).grid(column=0,row=0,sticky=N+W+E)
  Radiobutton(units_lb,text="MM",variable=units,value="mm"\
              ,command=autouintadjust).grid(column=1,row=0,sticky=N+W+E)
  units_lb.grid(column=0,row=5,columnspan=3,padx=2,pady=2,sticky=N+W+E)
  
  Label(fr,text="Pitch:")\
          .grid(column=0,row=6,padx=2,pady=2,sticky=N+E)
  pitch=StringVar(value="100")
  Entry(fr,textvar=pitch,width=20)\
          .grid(column=1,row=6,columnspan=2,padx=2,pady=2,sticky=N+W+E)
  
  Label(fr,text="Pad Dimension X:")\
          .grid(column=0,row=7,padx=2,pady=2,sticky=N+E)
  padx=StringVar(value="70")
  Entry(fr,textvar=padx,width=20)\
          .grid(column=1,row=7,columnspan=2,padx=2,pady=2,sticky=N+W+E)
  
  Label(fr,text="Pad Dimension Y:")\
          .grid(column=0,row=8,padx=2,pady=2,sticky=N+E)
  pady=StringVar(value="70")
  Entry(fr,textvar=pady,width=20)\
          .grid(column=1,row=8,columnspan=2,padx=2,pady=2,sticky=N+W+E)
  
  Label(fr,text="Pad Drill Diameter:")\
          .grid(column=0,row=9,padx=2,pady=2,sticky=N+E)
  paddrill=StringVar(value="35")
  Entry(fr,textvar=paddrill,width=20)\
          .grid(column=1,row=9,columnspan=2,padx=2,pady=2,sticky=N+W+E)

  Label(fr,text="Pin Row Spacing X:")\
          .grid(column=0,row=10,padx=2,pady=2,sticky=N+E)
  rowx=StringVar(value="0")
  rowx_e = Entry(fr,textvar=rowx,width=20)
  rowx_en = lambda: \
    rowx_e.grid(column=1,row=10,columnspan=2,padx=2,pady=2,sticky=N+W+E)
  rowx_di = lambda: \
    rowx_e.grid_forget()
  rowx_en()
  rowx_di()

  Label(fr,text="Pin Row Spacing Y:")\
          .grid(column=0,row=11,padx=2,pady=2,sticky=N+E)
  rowy=StringVar(value="0")
  rowy_e = Entry(fr,textvar=rowy,width=20)
  rowy_en = lambda: \
    rowy_e.grid(column=1,row=11,columnspan=2,padx=2,pady=2,sticky=N+W+E)
  rowy_di = lambda: \
    rowy_e.grid_forget()
  rowy_en()
  rowy_di()
  
  padshp_lb=ttk.Labelframe(fr,text="Pad Shape",padding=2)
  padshape=StringVar(value="C")
  Radiobutton(padshp_lb,text="Circle",variable=padshape,value="C")\
          .grid(column=0,row=0,sticky=N+W+S)
  Radiobutton(padshp_lb,text="Rectangle/Square",variable=padshape,value="R")\
          .grid(column=1,row=0,sticky=N+W+S)
  Radiobutton(padshp_lb,text="Oblong",variable=padshape,value="O")\
          .grid(column=3,row=0,sticky=N+W+S)
  padshp_lb.grid(column=0,row=12,columnspan=3,padx=2,pady=2,sticky=N+W+E)

  firstpinsquare = BooleanVar()
  Checkbutton(fr,text="First Pin Square",variable=firstpinsquare,\
           onvalue=True,command=draw)\
           .grid(column=0,row=13,padx=2,pady=2,sticky=N+W+S)
  
  locking = BooleanVar()
  Checkbutton(fr,text="Self Locking Formation",\
     variable=locking,onvalue=True,command=draw)\
     .grid(column=1,row=13,padx=2,pady=2,columnspan=2,sticky=N+W+S)

  padtyp_lb=ttk.Labelframe(fr,text="Pad Type",padding=2)
  padtype=StringVar(value="STD")
  Radiobutton(padtyp_lb,text="Through Hole",variable=padtype,value="STD")\
          .grid(column=0,row=0,sticky=N+W+S)
  Radiobutton(padtyp_lb,text="SMD",variable=padtype,value="SMD")\
          .grid(column=1,row=0,sticky=N+W+S)  
  padtyp_lb.grid(column=0,row=14,columnspan=3,padx=2,pady=2,sticky=N+W+E)
  
  Label(fr,text="Description:")\
          .grid(column=0,row=15,padx=2,pady=2,sticky=N+E)
  description=StringVar(value="Description")
  Entry(fr,textvar=description,width=40)\
          .grid(column=1,row=15,columnspan=2,padx=2,pady=2,sticky=N+W+E)
  
  Label(fr,text="Keywords:")\
          .grid(column=0,row=16,padx=2,pady=2,sticky=N+E)
  keywords=StringVar(value="Key1 Key_2")
  Entry(fr,textvar=keywords,width=20)\
          .grid(column=1,row=16,columnspan=2,padx=2,pady=2,sticky=N+W+E)  
############################################################################
def Draw_ConvertPane(fr):
  """To Generate the Content for the Converter Frame"""
  Label(fr,text="mm to Mil Converter",justify="center")\
          .grid(column=0,row=0,columnspan=3,padx=2,pady=2,sticky=N+E+W)
  Label(fr,text="mm")\
          .grid(column=0,row=2,padx=2,pady=2,sticky=N+E)
  mm=StringVar(value="0")
  Entry(fr,textvar=mm,width=10)\
          .grid(column=1,row=2,padx=2,pady=2,sticky=N+W+E)
  Label(fr,text="Mils")\
          .grid(column=0,row=3,padx=2,pady=2,sticky=N+E)
  mil=StringVar(value="0")
  Entry(fr,textvar=mil,width=10,state="readonly")\
          .grid(column=1,row=3,padx=2,pady=2,sticky=N+W+E)
  def handler(mm,mil):
    try:
      m = float(mm.get())*(1000/25.4)
      mil.set("%f"%m)
    except:
      mm.set("0")
      
  Button(fr,text="Convert",command=lambda:handler(mm,mil))\
          .grid(column=3,row=2,padx=2,pady=2,sticky=N+W+E+S)

  Label(fr,text="Mil to mm Converter",justify="center")\
          .grid(column=0,row=4,columnspan=3,padx=2,pady=2,sticky=N+E+W)
  Label(fr,text="Mils")\
          .grid(column=0,row=6,padx=2,pady=2,sticky=N+E)
  mil1=StringVar(value="0")
  Entry(fr,textvar=mil1,width=10)\
          .grid(column=1,row=6,padx=2,pady=2,sticky=N+W+E)
  Label(fr,text="mm")\
          .grid(column=0,row=7,padx=2,pady=2,sticky=N+E)
  mm1=StringVar(value="0")
  Entry(fr,textvar=mm1,width=10,state="readonly")\
          .grid(column=1,row=7,padx=2,pady=2,sticky=N+W+E)
  def handler1(mm,mil):
    try:
      m = float(mil.get())*(25.4/1000)
      mm.set("%f"%m)
    except:
      mil.set("0")
      
  Button(fr,text="Convert",command=lambda:handler1(mm1,mil1))\
          .grid(column=3,row=6,padx=2,pady=2,sticky=N+W+E+S)
############################################################################
def Draw_PicturePane(fr):
  """To Generate the Content for the Picture Frame"""
  global canvas
  canvas = Canvas(fr,width=200,height=200,background="white")
  canvas.pack(fill=BOTH)
############################################################################
def Draw_CommandPane(fr):
  """To Generate the Content for the Command & Buttons Frame"""
  status = StringVar(value="""Designed by: A.D.H.A.R Labs Research,Bharat(India)
Abhijit Bose( info@adharlabs.in )
http://m8051.blogspot.com
License:CC BY-NC-SA 3.0""")
  Label(fr,text="",textvariable=status)\
        .grid(column=0,row=0,rowspan=2,padx=40,pady=2,sticky=N+E+W+S)

  Button(fr,text="Auto Generate Names",command=autoname )\
          .grid(column=1,row=0,padx=20,pady=2)

  gentogether = BooleanVar()
  ck = Checkbutton(fr,text="Generate Module & Lib",variable=gentogether,\
                   onvalue=True)
  ck.grid(column=1,row=1,padx=2,pady=2,sticky=N+W+S)
  gentogether.set(True)
  
  Button(fr,text="Generate Lib",width=10,command=packed)\
                        .grid(column=2,row=0,padx=2,pady=2)
  
  Button(fr,text=" Exit Prog ",width=10,command=lambda:root.destroy())\
                        .grid(column=2,row=1,padx=2,pady=2)

  
############################################################################
# Main FUNCTION>
############################################################################
if __name__ == "__main__" :
  #{
  global meta       
         
  meta = {}
  print(__doc__)
  ## Create Main Window
  root = Tk()
  root.title("Kicad Module Generator v"+__version__+\
             " by A.D.H.A.R Labs Research,Bharat(India) ")  
  root.bind("<Escape>",lambda e:root.destroy())
  root["padx"]=10
  root["pady"]=10
  #  { MAIN CONTENT BEGIN
  content = Frame(root,width=300,height=200,borderwidth=2,relief="groove")
  #    { DATAFRAME 1 BEGIN
  note = ttk.Notebook(content,padding=2)
  data_frm1 = Frame(note,width=200,height=200,borderwidth=3,\
                    relief="ridge",padx=2,pady=2)
  Draw_MainPane(data_frm1)
  #data_frm1.grid(column=0,row=0,rowspan=2,padx=5,pady=5)
  note.add(data_frm1,text="Module Generator",padding=5)
  note.grid(column=0,row=0,rowspan=2,padx=5,pady=5)
  #    } DATA FRAME 1 END
  #    { DATA FRAME 2 BEGIN
  data_frm2 = Frame(content,width=200,height=200,borderwidth=3,\
                    relief="ridge",padx=2,pady=2)
  Draw_PicturePane(data_frm2)
  data_frm2.grid(column=1,row=0,padx=5,pady=5,sticky=N+W+E+S)
  #    } DATA FRAME 2 END
  #    { DATA FRAME 3 BEGIN
  data_frm3 = Frame(content,width=200,height=200,borderwidth=3,\
                    relief="ridge",padx=2,pady=2)
  Draw_ConvertPane(data_frm3)  
  data_frm3.grid(column=1,row=1,padx=5,pady=5,sticky=N+W+E+S)
  #    } DATA FRAME 3 END
  #    { DATA FRAME 4 BEGIN
  data_frm4 = Frame(content,padx=2,pady=2)
  Draw_CommandPane(data_frm4)
  data_frm4.grid(column=0,row=2,columnspan=2,padx=5,pady=5,sticky=N+W+E+S)
  #    } DATA FRAME 4 END
  content.grid(column=0,row=0,sticky=N+S+E+W)
  # Update all Data
  package_cmb_update(None)
  #  }
  ## Main Loop Start
  root.mainloop()
  #}
############################################################################
