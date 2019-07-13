#-----------------------------------------------------------
# RainbowChainAddon.py
#
# Version 0.9, under development
#
# Copyright (C) 2019, Michael Trösch aka Farbigewelt
#
# The script adds a panel in '3D View - Tools - Array One'. Object array  
# added with RainbowChainAddon.py can be changed in the panel user interface.
# Parameters/properties like e.g. radius or step can be adjusted interactively.
# Array's objects' default locations are defined in presets. Parameters can 
# be keyed for animations. Any active object can be used to be added in an array.

# 
# Software "RainbowChainAddon" comes with Aboslutely No Warranty, 
# read details in "LICENSE - GPL 3.txt". 
#
# This is free software. You are welcome to use, 
# modify, redistribute it under certain conditions.
#
#------------------------------------------------------------
#
# Read abc.<something> as to replace expression <something> by 
# e.g. character, i.e. abc.character. Another example:
# doIt(text='<property name>' means e.g. doIt(text='prop_string'.

# bl_info is minimal requirement for any Blender Pyhton add-on.
bl_info = {
    "name": "Rainbow Chains",
    "author": "Michael Trösch (FarbigeWelt)",
    "version": (0, 9),
    "blender": (2, 79, 0),
    "location": "View3D > Tools > Array One",
    "description": "Adds an array of active objects copies. UI interaction \
or animation keys change array",
    "category": "Object",
}

import bpy
from bpy.app.handlers import persistent
import random
import math
import time


# There are 4 pattern presets. One can add further patterns with code adjustments.
# To add further patterns extent the code close to each of the following FIVE comments.
# Add your own pattern name above between 
# Add your own pattern parameters above between
# Add your own pattern method below 
# Add your own pattern selection below 
# Add your own pattern method call below
# Search for above comments in the code and extent as descripted. Do not remove
# the comment lines for obvious reasons.


class DataContainer():
    def __init__(self):
# 'Cube' is default name of bpy.ops.mesh.primitive_cube_add(().
# Use of default name may lead to unexpected results of RainbowChainAddon,
# especially if there are other 'Cube' named objects in the scene.
        self.object_name="Objects"
# digits sets the number of characters including integer 0 to 6. Object
# names must have leading zeros and continuos increasing integers.
# Example: Suffix of 'Objects.0007' has 4 digits, 3 leading zeros and
# a one digit number. 
        self.digits=4
# Set name of your BlendLuxCore material. The material must use an
# "Object ID" node as color input for e.g. diffuse color. A Material without
# "Object ID" node cannot render different colored cubes with RainbowChainPanel.
        self.material_name='Matte.ID'
        self.material=bpy.types.Material
# Standard object size is 1. Because object array added is usually between
# 10*10 and 40*40 reducing makes sense. Object size and axis offsets are scaled
# by scale_factor. Factors value is adjusted automatically to get an array object 
# size of approx. 1. This way camera (distance to object, focal length) 
# can be fix for any x*y array.
        self.scale_factor=0.1
# Following flags, in combination with look up of previous values, are used
# to avoid redrawing if parameters have not changed but frame has changed.
        self.drawing_ongoing=False
        self.handler_called=False

        self.frame_current=1
        self.frame_current_old=self.frame_current
            
        self.patterns = [
            ("CLOUD", "Cloud", "", 1),
            ("SINCOS", "SinCos", "", 2),
            ("GAUSS", "Gauss", "", 3),
            ("BOID", "Boid", "", 4),
            ]
# Add your own pattern name above between the square brackets in a new like.
        self.pattern_selection="CLOUD"
        self.pattern_selection_old=self.pattern_selection="CLOUD"
        self.pattern_isInit=False

# Read the values from the user interface in the following order
# ("Inner",<Number of Loops>,Step Width>,<Frequency>,<Radius>,<Offset>)
        self.parameters=[
            ("Cloud",("Inner",30,1,1,30,1.5),("Outer",30,1,0.5,30,0)),
            ("SinCos",("Inner",30,1,0.5,30,-1.5),("Outer",30,1,0.5,30,0)),
            ("Gauss",("Inner",30,0.5,0,30,-7.5),("Outer",30,0.5,1.25,30,-7.5)),
            ("Boid",("Inner",30,0.05,1,30,-0.6),("Outer",30,0.05,1,30,-0.6)),
            ]
# Add your own pattern parameters above between the square brackets in a new like.
#           ("PatternName",("Inner",30,0.05,1,30,-0.6),("Outer",30,0.05,1,30,-0.6)),
# Note: 'PatternName', 'Inner' and 'Outer' are used only to improve readability.
        
        self.min=2**-126
        self.max=2**127
        
    def update(self):
        scene=bpy.context.scene
        self.frame_current=scene.frame_current
# Get specific material as object from bpy.data library
        self.material= bpy.data.materials.get(self.material_name)  
        self.pattern_selection=scene.select_pattern      
    
    def store(self,frame,pattern):
        scene=bpy.context.scene
        self.frame_current_old=frame
        self.pattern_selection_old=pattern
        
    def checkChangedProps(self):
        scene=bpy.context.scene
        flag1=self.frame_current_old==scene.frame_current
        flag2=self.pattern_selection_old==self.pattern_selection

        return True and flag1 and flag2


class Color:
    def __init__(self,byte):
        self.factor=pow(2,((byte-1)*8))
        self.colors=[]
        self.min=0
        self.max=255
        for count in range(self.min, self.max+1,1):
            self.colors.append(count*self.factor)

    def value(self,index):
        return self.colors[index]


# Use example of Colors
# >>>colors=Colors()
# >>>colors.Rgb(red,green,blue)
# red+green*256+blue*256^2      as decimal output
class RgbColor:
    """Calculates 3 Byte RGB value"""
    def __init__(self):
        self.red=Color(1)
        self.green=Color(2)
        self.blue=Color(3)
            
    def Rgb(self,red,green,blue):
        return self.red.value(red)+self.green.value(green)+self.blue.value(blue)


# Method eval() calculates rainbow color depending on integer value
class RainbowColor:
    color=0
    def eval(self,value):
        max=255
        current=value%256
        value=value%1536
        if value<256:
            self.color=color.Rgb(max,current,0)
        elif value<512:
            self.color=color.Rgb(max-current,max,0)
        elif value<768:
            self.color=color.Rgb(0,max,current)
        elif value<1024:
            self.color=color.Rgb(0,max-current,max)
        elif value<1280:
            self.color=color.Rgb(current,0,max)
        elif value<1536:
            self.color=color.Rgb(max,0,max-current)

        return self.color


class LoopData():
# Example use: x=sin(frequency*angle)*radius 
# frequency   turns/s=2*pi/s=360°/s
# min to max defines range of loop with step width step
# for i in range(min,max,1) are max-min steps, last i=max-1
    def __init__(self,loops,step,freq,radius,offset):
        self.loops_default=loops
        self.step_default=step
        self.freq_default=freq
        self.radius_default=radius
        self.offset_default=offset
        
        self.min=0
        self.count_steps=0
        self.random_offset=0.02

        self.loops=self.loops_default
        self.step=self.step_default
        self.freq=self.freq_default
        self.radius=self.radius_default
        self.offset=self.offset_default

        self.max=self.loops*self.step
        self.range=self.max-self.min

        self.loops_old=self.loops_default
        self.step_old=self.step_default
        self.freq_old=self.freq_default
        self.radius_old=self.radius_default
        self.offset_old=self.offset_default
    
        self.frame_current=1
        self.frame_current_old=1
        
# pass bpy.context.scene for scene
    def update(self,loops,step,freq,radius,offset):
        
        self.loops=loops
        self.step=step
        self.freq=freq 
        self.radius=radius   
        self.offset=offset   
        
        self.max=self.loops*self.step
        self.steps=self.max-self.min
        self.count_steps=0

        scene=bpy.context.scene
        self.frame_current=scene.frame_current
    
    def store(self,loops,step,freq,radius,offset):
        
        self.loops_old=loops
        self.step_old=step
        self.freq_old=freq 
        self.radius_old=radius
        self.offset_old=offset
        
    def checkChangedProps(self):
        scene=bpy.context.scene

        flag1=self.loops_old==scene.inner_step
        flag2=self.step_old==scene.inner_step
        flag3=self.freq_old==scene.inner_freq
        flag4=self.radius_old==scene.inner_radius
        flag5=self.offset_old==scene.inner_offset

        return True and flag1 and flag2 and\
                         flag3 and flag4 and flag5

# eval_y(x) calculates y based on x y=a*x+b.
# The function is used because number of loops and steps can be defined freely.
# Adjustable step width leads to variable maximum of inner and outer loop.
    def eval_y(self,x):
# x=counter
        self.x1=self.min
        self.x2=self.loops-1
        self.y1=1
        self.y2=self.loops*self.step
#        print("loops",self.loops,"step",self.step)
        self.a=(self.y2-self.y1)/(self.x2-self.x1)
        self.b=self.y2-self.a*self.x2
#        print("x",x,"a",self.a,"b",self.b)
        self.y=self.a*x+self.b
#        print("y1",self.y1,"y2",self.y2,"y",self.y)
        return self.y


class DrawObjects(bpy.types.Operator):
    """Draw Rainbow Chains"""
    bl_idname = "object.draw_objects"
    bl_label = "Draw Objects"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        drawObjects(self,context)
        return {'FINISHED'}


class AddObjects(bpy.types.Operator):
    """Add Rainbow Chain Objects"""
    bl_idname = "object.add_objects"
    bl_label = "Add Objects"

    def __init__(self):
        print("Set add object to False")
        bpy.types.Scene.add_objects=False

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        bpy.types.Scene.add_objects=True
        drawObjects(self, context)
        return {'FINISHED'}


# Properties' definitions see appendPropertiesToSceneContext().
# Use: row=context.scene.layout.row(), row.prop(scene,"<property name>")
# Parameter property is its name set in quotation marks. 
class LayoutPanel(bpy.types.Panel):
#"""Creates a Panel in the scene context of the properties editor"""
    bl_category = "Array One"
    bl_label = "Rainbow Chains"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'


    def draw(self, context):
        layout = self.layout

        scene = context.scene

        # Create a simple row.
        layout.label(text="Object Name: "+str(data.object_name))
        layout.label(text="Object Material: "+str(data.material_name))
        layout.label(text="Set Moves: "+str(inner.loops*outer.loops))
        layout.label(text="Objects availables: "+str(checkNumberOfObjects()))
        layout.label(text="Log: "+str(bpy.context.scene.log_text))

# Create an row where the properties are aligned to each other.
        row = layout.row(align=False)
# prop_menu_enum(data, property, text="")
        row.prop_menu_enum(scene, "select_pattern", text="Select a pattern.")
      
        layout.label(text="Number of Loops:")  
        row = layout.row(align=True)
        row.prop(scene,"inner_loops")          
        row.prop(scene,"outer_loops")

        layout.label(text="Step Width:")
        row = layout.row(align=True)
        row.prop(scene, "inner_step")
        row.prop(scene, "outer_step")

        layout.label(text="Frequency:")
        row = layout.row(align=True)
        row.prop(scene,"inner_freq")
        row.prop(scene,"outer_freq")
        
        layout.label(text="Radius:")
        row = layout.row(align=True)
        row.prop(scene,"inner_radius")          
        row.prop(scene,"outer_radius")

        layout.label(text="Offset:")
        row = layout.row(align=True)
        row.prop(scene,"inner_offset")
        row.prop(scene,"outer_offset")

        row = layout.row(align=True)
        row.prop(scene, "add_objects")
        row.prop(scene, "use_active")
# prop(anytype object, property, text="") 
# prop_search(data, property, search_data, search_property, text="")

# UI button for adding objects. Buttons are called operator in bpy.types.UILayout. 
# operator(<string>) requires a the bl_idname of a registered class. This class is
# required to use the @classmethod with  poll and execute method, see AddObjects(..).
# Because a button can be clicked unintentionally a solution is implemented
# that asks to check a flag box following an action like re-enter or 
# change UI property value.

#        layout.label(text="Add new Objects")
#        row = layout.row()
#        row.scale_y = 1.0
#        row.operator("object.add_objects")


# Defines method for a blender internal event handler. This handler
# might be called multiple times in a short time. Because drawObject() takes time
# this method avoids a following call before current drawimg is finished. 
@persistent
def post_handler(scene):
    scene=bpy.context.scene
    if data.handler_called==False:
        data.handler_called=True
        updateValues()
        print("Frame changed from", data.frame_current_old,"to",data.frame_current)
        if not checkChangedValues():
            print("At least one entry has changed. Starting scene redraw...")
# Pass drawObjects dummy parameters like (1,1) to meet method's definition (self,context).
# Functions called by property key 'update=' require self and context as paramter. 
            drawObjects(1,1)
        data.handler_called=False    
    else:
        print("post_handler called at least twice")
        for i in range(1,10):
            if data.handler_called:
                time.sleep(0.05)
            else:
                break
        data.handler_called=False

def timeCurrent():
    now = time.localtime() 
    time_text=leadingZerosText(2,"",now.tm_hour)+":"+\
                leadingZerosText(2,"",now.tm_min)+":"+\
                leadingZerosText(2,"",now.tm_sec)
    return time_text


def messageLog(message):
    scene=bpy.context.scene
    scene.log_text=str(timeCurrent())+" "+message
    print(scene.log_text)
    
    
def reportProgress(drawings_counter,print_after_drawings):
    count_max=inner.loops*outer.loops
    message=str('%5.1f' %(drawings_counter/count_max*100)+'% drawn, ')+\
            str(drawings_counter)+" objects"
    if drawings_counter%print_after_drawings==0:
# Prints drawing progress in percent to console
        messageLog(message)
    else:
        if not data.drawing_ongoing:
            messageLog(message)


# Check number of available objects containing object_name in name
def checkNumberOfObjects():
    counter=0
    for i in range(len(bpy.data.objects)):
        text=str(bpy.data.objects[i])
        pos_name=text.find(data.object_name)
        if pos_name != -1: 
            pos_bracket=text.find(")")
            if (pos_bracket-pos_name)==(len(data.object_name)+1):
                counter=counter+1
            else:
                pos_point=text.find(".")
                text_nr=text[pos_point+1:pos_bracket-1]
                if text_nr.isdigit():
                    counter=counter+1
    return counter


# Return a string with name only or name plus suffix number 
# with leading zeros. Method convert(..) requires text and integer (0,1,...).
# target digits including leading zero. number, integer between 0 and 10^6.
def leadingZerosText(digits,text,number):
    text_counter=""
    leading_zeros=""
    number_digits=0
    
    if number<1:
        text_counter=text
        number_digits=0
    elif number<1e1:
            number_digits=1         
    elif number<1e2:
            number_digits=2 
    elif number<1e3:
            number_digits=3 
    elif number<1e4:
            number_digits=4
    elif number<1e5:
            number_digits=5
    elif number<1e6:
            number_digits=6
                                
    for i in range(0,digits-number_digits,1):
        leading_zeros=leading_zeros+"0"
        
    if number==0:
        if len(text)==0:
            text_counter=leading_zeros
        else:
            text_counter=text
    else:
        if len(text)==0:
            text_counter=leading_zeros+str(number) 
        else:
            text_counter=text+"."+leading_zeros+str(number)
    
    return text_counter

# list: e.g. (1,2,3)    element: 1 to 3
def listMax(list,element):
    max=data.min
    if element>len(list):
        return float('nan')
    elif element<1:
        return float('nan')
    else:
        for i in list:
            e=i[element-1]
            if e>max:
                max=e
        return max

# list: e.g. (1,2,3)    element: 1 to 3
def listMin(list,element):
    min=data.max
    if element>len(list):
        return float('nan')
    elif element<1:
        return float('nan')
    else:
        for i in list:
            e=i[element-1]
            if e<min:
                min=e
        return min

def patternCloud(inner_count,outer_count):
    inner_cpr=inner_count/inner.range
    inner_angle=6.283*inner_cpr

    outer_cpr=outer_count/outer.range
    outer_angle=6.283*outer_cpr

    inner_value=inner.eval_y(inner_count)
    outer_value=outer.eval_y(outer_count)
    
    loops_value=inner_value*outer_value
    loops_cpr=loops_value/(inner.max*outer.max)
    loops_angle=6.283*loops_cpr
    
    x=math.sin(inner_angle*inner.freq)*inner.radius
    y=math.cos(inner_angle*inner.freq)*inner.radius
    x=x+math.sin(loops_angle*outer.freq)*outer.radius
    y=y+math.cos(loops_angle*outer.freq)*outer.radius

    z=inner_value%(inner.max+inner.step)*inner.offset

# Return resized axis offset. This is in accordance 
# with added objects size. 
    return (x*data.scale_factor,y*data.scale_factor,z*data.scale_factor) 


def patternSinCos(inner_count,outer_count):
    inner_cpr=inner_count/inner.range
    inner_angle=6.283*inner_cpr

    outer_cpr=outer_count/outer.range
    outer_angle=6.283*outer_cpr

    inner_value=inner.eval_y(inner_count)
    outer_value=outer.eval_y(outer_count)
    
    loops_value=inner_value*outer_value
    loops_cpr=loops_value/(inner.max*outer.max)
    loops_angle=6.283*loops_cpr

# Add +random.random()*<loop_type>.random_offset to get position variances.           
    x=inner_count
    y=outer_count
# z positions may depend on both x and y offsets. Center point is at position 
# (0,0,0) all other other points have at least one axis offset. 
    z=math.sin(inner_angle*inner.freq+inner.offset)**2*inner.radius+\
        math.cos(outer_angle*outer.freq+outer.offset)**2*outer.radius

    return (x*data.scale_factor,y*data.scale_factor,z*data.scale_factor) 


def patternGauss(inner_count,outer_count):
# sigma	s	1
# µ	        0
  	
#  d(s)                a(x),(µ,s)	b(x)	       c(x)	   var	g(x),(µ,s)
#  1/(s*sqrt(2*pi))    (x-µ)/s	   -1/2*a(x)^2	   e^b(x)	x	d(s)*c(x)

# math.exp(x)  Use ** or the built-in pow()for exact integer powers.
# math.pi    math.e      math.hypot(x, y) Return the Euclidean norm, sqrt(x*x + y*y).
    x=inner_count+inner.offset
    y=outer_count+outer.offset
    s=outer.freq
    mu=inner.freq
    d=1/(s*math.sqrt(2*math.pi))
    x_a=(x-mu)/s
    x_b=-0.5*x_a**2
    x_c=math.exp(x_b)
    x_g=d*x_c
    y_a=(y-mu)/s
    y_b=-0.5*y_a**2
    y_c=math.exp(y_b)
    y_g=d*y_c
    z=x_g*inner.radius+y_g*outer.radius
    
    return (x*data.scale_factor,y*data.scale_factor,z*data.scale_factor) 


def patternBoid(inner_count,outer_count):
    inner_cpr=inner_count/inner.range
    inner_angle=6.283*inner_cpr

    outer_cpr=outer_count/outer.range
    outer_angle=6.283*outer_cpr

    inner_value=inner.eval_y(inner_count)
    outer_value=outer.eval_y(outer_count)
    
    loops_value=inner_value*outer_value
    loops_cpr=loops_value/(inner.max*outer.max)
    loops_angle=6.283*loops_cpr
    
#    x=math.sin(inner_angle*inner.freq)*inner.radius+inner.offset
#    y=math.cos(inner_angle*inner.freq)*inner.radius+inner.offset

    x=inner_count
    y=outer_count

    z=-(inner.radius*(x+inner.offset)**2+outer.radius*(y+outer.offset)**2)

    x=inner_count*inner.radius
    y=outer_count*outer.radius
    
# Return resized axis offset. This is in accordance 
# with added objects size. 
    return (x*data.scale_factor,y*data.scale_factor,z*data.scale_factor) 


# Add your own pattern method below this comment lines in the following style.
# def patternOwnMethod(inner_count,outer_count):
# ... code to calculate x,y,z ...
#   return (x*data.scale_factor,y*data.scale_factor,z*data.scale_factor) 

def patternInitAndDraw(self, context):
    data.pattern_isInit=True
    scene=bpy.context.scene
    pattern=scene.select_pattern
    if pattern=="CLOUD":
        parameter=data.parameters[0]
    elif pattern=="SINCOS":
        parameter=data.parameters[1]
    elif pattern=="GAUSS":
        parameter=data.parameters[2]
    elif pattern=="BOID":
        parameter=data.parameters[3]
# Add your own pattern selection below this comment lines like
#   elif pattern=="PATTERNNAME":
#       parameter=data.parameters[4]

    scene.inner_loops=parameter[1][1]
    scene.inner_step=parameter[1][2]
    scene.inner_freq=parameter[1][3]
    scene.inner_radius=parameter[1][4]
    scene.inner_offset=parameter[1][5]

    scene.outer_loops=parameter[2][1]
    scene.outer_step=parameter[2][2]
    scene.outer_freq=parameter[2][3]
    scene.outer_radius=parameter[2][4]
    scene.outer_offset=parameter[2][5]
    
    data.pattern_isInit=False
    drawObjects(1,1)

def drawObjects(self, context):
    scene=bpy.context.scene
    objects_available=checkNumberOfObjects()
    if not scene.add_objects:
        if objects_available==0:
            return
    if data.pattern_isInit:
        return
    
    data.update()
    updateValues()

    drawings_counter=0
# Print progress after each number of drawings
    print_after_drawings=100
    reportProgress(drawings_counter,print_after_drawings)
    data.drawing_ongoing=True

# Counter to count total nr. of drawings (inner and outer loop)
    drawings_counter=1
    drawings_max=inner.loops*outer.loops
    origins=[]

# Outer loop can be seen as loop for y positions.
    outer_counter=0
    outer_count=outer.min
    while outer_count<outer.max:
# Check if all existing objects have been moved already because
# product of loops' user entries is allowed to exceed number of objects.
        if not scene.add_objects:
            if objects_available<(drawings_counter-1+inner.loops):
                break
# Inner loop can bee seen as loop for x positions.
        inner_counter=0
        inner_count=inner.min
        while inner_count<inner.max:
        
            if data.pattern_selection=="CLOUD":
                origin=patternCloud(inner_count,outer_count)
            elif data.pattern_selection=="SINCOS":
                origin=patternSinCos(inner_count,outer_count)
            elif data.pattern_selection=="GAUSS":
                origin=patternGauss(inner_count,outer_count)                
            elif data.pattern_selection=="BOID":
                origin=patternBoid(inner_count,outer_count)
# Add your own pattern method call below this comment lines like
#            elif data.pattern_selection=="PATTERNNAME":
#                origin=patternOwnPattern(inner_count,outer_count)
                                       
            origins.append(origin)
            
            drawings_counter=drawings_counter+1
            inner_counter=inner_counter+1
            inner_count=inner_count+inner.step
            
        outer_counter=outer_counter+1
        outer_count=outer_count+outer.step

    z_max=listMax(origins,3)
    z_min=listMin(origins,3)
    if abs(z_max)>abs(z_min):
        z_abs=abs(z_max)
    else:
        z_abs=abs(z_min)

    drawings_counter=1
    outer_counter=0
    outer_count=outer.min
    while outer_count<outer.max:
        if not scene.add_objects:
            if objects_available<(drawings_counter-1+inner.loops):
                break
        inner_counter=0
        inner_count=inner.min
        while inner_count<inner.max:

            object_name_numbered=leadingZerosText(data.digits,\
                                data.object_name,drawings_counter)           
            
            origin=origins[drawings_counter-1]
            x=origin[0]
            y=origin[1]
            z=origin[2]

# Check if z_abs is zero to avoid divison by zero
            if not z_abs==0:
                color=rainbow_color.eval(int(z/z_abs*drawings_max))
            else:
                color=rainbow_color.eval(0)
                        
            if bpy.context.scene.add_objects:
                addObjectsAndAppendMaterial(data.material,origin,\
                                        color,object_name_numbered)
            else:
                bpy.data.objects[object_name_numbered].location.x = x
                bpy.data.objects[object_name_numbered].location.y = y
                bpy.data.objects[object_name_numbered].location.z = z
                bpy.data.objects[object_name_numbered].luxcore.id = color

            drawings_counter=drawings_counter+1
            inner_counter=inner_counter+1
            inner_count=inner_count+inner.step
            reportProgress(drawings_counter-1,print_after_drawings)
            
        outer_counter=outer_counter+1
        outer_count=outer_count+outer.step       
        
# All objects added set flag to False
    scene.add_objects=False
    data.handler_called=False
            
# update scene due to new position of the objects
    bpy.context.scene.update()
    data.drawing_ongoing=False
    reportProgress(drawings_counter-1,print_after_drawings)
    print_counter=0
    storeOldValues()


# Append a property of different types to bpy.types.Scene 
# Acess value of property with bpy.context.scene.property_name
# Use property e.g. for UI layout. 
# bpy.types.Panel.layout.row.prop requires object of any type 
# and name of property.
def appendPropertiesToSceneContext():
    bpy.types.Scene.log_text=bpy.props.StringProperty(name="Log",\
        default="")

# bpy.props.EnumProperty requires a list of items, see data.patterns.
# Property can be showed with row.prop_menu_enum(), see LayoutPanel.
    bpy.types.Scene.select_pattern = bpy.props.EnumProperty(name='Select Pattern',\
        items=data.patterns,\
        description="Select Pattern. Each pattern sets\
position of the cubes differently, just try them :-).",\
        default="CLOUD",\
        update=patternInitAndDraw)

    bpy.types.Scene.inner_loops = bpy.props.IntProperty(name="Inner",\
        description="First of two loops. Range 1 to Inner: with \
adjustable step width.",\
        default=outer.loops_default,\
        min=1, max=128,\
        soft_min=1,soft_max=128,\
        update=drawObjects)
    bpy.types.Scene.outer_loops = bpy.props.IntProperty(name="Outer",\
        description="Second of two loops. Range 1 to Outer: with \
adjustable step width.",\
        default=inner.loops_default,\
        min=1, max=128,\
        soft_min=1, soft_max=128,\
        update=drawObjects)

    bpy.types.Scene.inner_step = bpy.props.FloatProperty(name="Inner",\
        description="Step width of Inner loop. Step is an integer number.",\
        default=inner.step_default,\
        min=0.01, max=int(inner.loops),\
        soft_min=0.01, soft_max=int(inner.loops),\
        step=1, precision=2, update=drawObjects)             
    bpy.types.Scene.outer_step = bpy.props.FloatProperty(name="Outer",\
        description="Step width of Outer loop. Step is an integer number.",\
        default=outer.step_default,\
        min=0.01, max=int(outer.loops),\
        soft_min=0.01, soft_max=int(outer.loops),\
        step=1, precision=2, update=drawObjects)

    bpy.types.Scene.inner_freq = bpy.props.FloatProperty(name="Inner",\
        description="Change frequency of inner function: f(n)=fn(freq*n+offset)*radius.",\
        default=inner.freq_default,\
        min=-1000, max=1000,\
        soft_min=-1000, soft_max=1000,\
        step=3, precision=2, update=drawObjects)
    bpy.types.Scene.outer_freq = bpy.props.FloatProperty(name="Outer",\
        description="Change frequency of outer function: f(n)=fn(freq*n+offset)*radius.",\
        default=outer.freq_default,\
        min=-1000, max=1000,\
        soft_min=-1000, soft_max=1000,\
        step=3, precision=2, update=drawObjects)

    bpy.types.Scene.inner_radius = bpy.props.FloatProperty(name="Inner",\
        description="Change radius of inner function: f(n)=fn(freq*n+offset)*radius.",\
        default=inner.radius_default,\
        min=0.1, max=100,\
        soft_min=0.1, soft_max=100,\
        step=3, precision=1, update=drawObjects)        
    bpy.types.Scene.outer_radius = bpy.props.FloatProperty(name="Outer",\
        description="Change radius of outer function: f(n)=fn(freq*n+offset)*radius.",\
        default=outer.radius_default,\
        min=0.1, max=100,\
        soft_min=0.1, soft_max=100,\
        step=3, precision=2, update=drawObjects)

    bpy.types.Scene.inner_offset = bpy.props.FloatProperty(name="Inner",\
        description="Change offset of inner function: f(n)=fn(freq*n+offset)*radius.",\
        default=inner.offset,\
        min=-100, max=100,\
        soft_min=-100, soft_max=100,\
        step=3, precision=2, update=drawObjects)        
    bpy.types.Scene.outer_offset= bpy.props.FloatProperty(name="Outer",\
        description="Change offset of outer function: f(n)=fn(freq*n+offset)*radius.",\
        default=outer.offset,\
        min=-100, max=100,\
        soft_min=-100, soft_max=100,\
        step=3, precision=2, update=drawObjects)
        
    bpy.types.Scene.add_objects = bpy.props.BoolProperty(name=\
        'Add objects.',\
        description="Add Objects, default is not checked. Adds objects product of both \
loops time if any of the parameters has been changed or re-entered. \
(Unchecks automatically after objects have been added.)",\
        default=False) 

    bpy.types.Scene.use_active = bpy.props.BoolProperty(name=\
        'Use active.',\
        description="Use active objective, default is not checked. Unchecks \
automatically if Add objects is not checked. Copies active object product of \
both loops times if both boxes are checked any of the parameters has \
been changed or re-entered.)",\
        default=False) 


def updateValues():
# store values for comparison if update is required
    scene=bpy.context.scene

    inner.update(scene.inner_loops,scene.inner_step,\
            scene.inner_freq,scene.inner_radius,scene.inner_offset)
    outer.update(scene.outer_loops,scene.outer_step,\
            scene.outer_freq,scene.outer_radius,scene.outer_offset)

# use_active makes sense only in combination with true add_object
    if not scene.add_objects:
        scene.use_active=False
        
def storeOldValues():
# store values for comparison if update is required
    scene=bpy.context.scene

    inner.store(inner.loops,inner.step,inner.freq,inner.radius,inner.offset)
    outer.store(outer.loops,outer.step,outer.freq,outer.radius,outer.offset)
    data.store(data.frame_current,data.pattern_selection)

def checkChangedValues():

    flag1=inner.checkChangedProps()
    flag2=outer.checkChangedProps() 
    flag3=data.checkChangedProps()
    
    return True and flag1 and flag2 and \
                    flag3 
 
   
def addObjectsAndAppendMaterial(material,origin,color,name_numbered):
# Calculate a random x,y,z rotation point and apply it to a new cube object.
    r1=random.random()
    r2=random.random()
    r3=random.random()
    
    def addPrimitive():
        rotation=(r1,r2,r3)
        bpy.ops.mesh.primitive_cube_add(location=origin,\
                rotation=rotation,radius=data.scale_factor)
        return bpy.context.active_object
    
# Creates a list with the name of all selected objects.
    scene=bpy.context.scene
#    names_of_selected_objects = [obj.name for obj in bpy.context.selected_objects]
    if scene.use_active:
# Sets property back to false after use.
        scene.use_active=False
        active_object=bpy.context.active_object
#        if len(names_of_selected_objects)>0:
        if len(active_object.name)>0:
            object=active_object.copy()
            object.data=active_object.data.copy()
            object.animation_data_clear()
            object.scale.x=data.scale_factor
            object.scale.y=data.scale_factor
            object.scale.z=data.scale_factor
            object.rotation_euler.x=r1
            object.rotation_euler.y=r2
            object.rotation_euler.z=r3
            scene.objects.link(object)
    else:
        object=addPrimitive()

# Set LuxCoreRender object ID with 3 Byte color value of use with material node.
    object.luxcore.id=color
# Change name of the object.
    object.name = name_numbered
    object.data.name = name_numbered
# Append specific material to cube.
    object.data.materials.append(material)


def setPropertiesUI():
# store values for comparison if update is required
    scene=bpy.context.scene
    inner.radius_old=scene.inner_radius
    outer.radius_old=scene.outer_radius
    inner.step_old=scene.inner_step
    outer.step_old=scene.outer_step
    inner.freq_old=scene.inner_freq
    outer.freq_old=scene.outer_freq
    inner.frame_current_old=scene.frame_current


def register():
    bpy.utils.register_class(DrawObjects)
    bpy.utils.register_class(LayoutPanel)
    bpy.utils.register_class(AddObjects)
# Define UI properties in bpy.types.Scene. To get/set their value use
# bpy.context.scene.
    appendPropertiesToSceneContext()
    print("class registered")
# Append method to blender event handler'frame:change_post'.
    bpy.app.handlers.frame_change_post.append(post_handler)


def unregister():
    bpy.utils.unregister_class(DrawObjects)
    bpy.utils.unregister_class(LayoutPanel)
    bpy.utils.unregister_class(AddObjects)
# Remove method from blender event handler'frame:change_post'.
    bpy.app.handlers.frame_change_post.remove(post_handler)
    
    Scene=bpy.types.Scene
    bpy.props.RemoveProperty(Scene,attr='log_text')
    bpy.props.RemoveProperty(Scene,attr='select_pattern')
    bpy.props.RemoveProperty(Scene,attr='inner_step')
    bpy.props.RemoveProperty(Scene,attr='inner_freq')
    bpy.props.RemoveProperty(Scene,attr='inner_radius')
    bpy.props.RemoveProperty(Scene,attr='inner_offset')
    bpy.props.RemoveProperty(Scene,attr='outer_step')
    bpy.props.RemoveProperty(Scene,attr='outer_freq')
    bpy.props.RemoveProperty(Scene,attr='outer_radius')
    bpy.props.RemoveProperty(Scene,attr='outer_offset')
    bpy.props.RemoveProperty(Scene,attr='add_objects')
    bpy.props.RemoveProperty(Scene,attr='use_active')


# Following lines are required to to run the script from text editor 
# without the need to install the script. This is very usefull for testing.
if __name__ == "__main__":
    register()


# Instantiate data object for 'global variables'.
data=DataContainer()

# Use: colors=Colors(); color=colors.Rgb(red,green,blue)
color = RgbColor()

# Method eval(self,value) calculates rainbow color.
# value is integer.
rainbow_color=RainbowColor()

# Instantiate objects for inner and outer loop controlling.
# These objects are important e.g. to act flexible on user input.
# defaults: loops,step,freq,radius,offset

parameter=data.parameters[0]

inner_loops=parameter[1][1]
inner_step=parameter[1][2]
inner_freq=parameter[1][3]
inner_radius=parameter[1][4]
inner_offset=parameter[1][5]

outer_loops=parameter[2][1]
outer_step=parameter[2][2]
outer_freq=parameter[2][3]
outer_radius=parameter[2][4]
outer_offset=parameter[2][5]

inner=LoopData(inner_loops,inner_step,inner_freq,inner_radius,inner_offset)
outer=LoopData(outer_loops,outer_step,outer_freq,outer_radius,outer_offset)