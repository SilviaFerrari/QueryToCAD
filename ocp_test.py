import cadquery as cq
from ocp_vscode import show, set_port, set_defaults

# viewer configuration communication channel
set_port(3939) 

# forces OCP to show grids and axes
set_defaults(axes=True, axes0=True, grid=(True, True, True))

# create a simple cube with a hole
result = (cq.Workplane("XY") # we have to chose a working plane
          .box(10, 10, 10) # draw a cube in the origin
          .faces(">Z") # select the top face of the cube
          .workplane() # create a new working plane
          .hole(5)) # create the hole

print("Geometria generata con successo!")

# sending the code to the viewer with a name and a color
show(result, names=["Cubo_Test"], colors=["red"])