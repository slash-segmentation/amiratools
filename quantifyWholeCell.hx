# Amira

#//
# Function: exportCSV
# -----------------------------------
# Exports data from a Spatial Graph or Geometry Surface object to a CSV file
#
# Inputs:
#     moduleIn    Name of the Spatial Graph object
#     moduleOut   Name of the output statistics object
#     fileOut     Name of output CSV file
#//

proc exportCSV {moduleIn moduleOut fileOut} {
    set tableName [split $moduleIn "."]
    set tableName [lindex $tableName 0]
    if {$tableName == "GeometrySurface"} {
        create HxSurfaceArea $moduleOut
    } elseif {$tableName == "SmoothTree"} {
        create HxSpatialGraphStats $moduleOut
    }
    append tableName ".statistics"
    $moduleOut data connect $moduleIn
    $moduleOut doIt snap
    $moduleOut fire
    $tableName exportData "CSV" $fileOut
}

#//
# Function: makeCameraOrbitEvent
# ------------------------------
# Generates a single classic Demo Maker event string that performs rotation of an
# object by a specified number of degrees across a given time interval.
#
# Inputs:
#     type      String specifying the object type (i.e. "Camera-Orbit")
#     N         Integer specifying the number of the object type
#     time1     Time to start the rotation
#     time2     Time to end the rotation
#     angle1    Angle to begin the rotation at (in degrees)
#     angle2    Angle to end the rotation at 
#
# Returns:
#     str       Event string
#//

proc makeCameraOrbitEvent {type N time1 time2 angle1 angle2} {
    set str "dummy {numeric {$type-$N/Time} $time1 $time2 $angle1 $angle2 0 360 "
    append str "{\"$type-$N\" time setValue %0%; \"$type-$N\" fire}} "
    return $str
}
#//
# Function: makeMaskEvent
# -----------------------
# Generates a single classic Demo Maker event string that either toggles on or toggles
# off the display of an object at a single time point.
#
# Inputs:
#     type     String specifying the object type (i.e. "Surface-View")
#     N        Integer specifying the number of the object type
#     time     Time to perform the toggle
#     state    Specifies whether the object is turned on ( = 1) or off ( = 0)
#
# Returns:
#     str      Event string
#//

proc makeMaskEvent {type N time state} {
    set str "dummy {toggle {$type-$N/Viewer mask/Viewer 0} $time $state "
    append str "{\"$type-$N\" setViewerMask %0%}} "
    return $str
}

#//
# Function: makeSliceNumberEvent
# ------------------------------
# Generates a single classic Demo Maker event string that plays through the given slices 
# of an ortho slice object over a given time interval.
#
# Inputs:
#     type      String specifying the object type (i.e. "Ortho-Slice")
#     N         Integer specifying the number of the object type
#     time1     Time to start playing through the slices
#     time2     Time to end playing through the slices
#     slice1    Slice of the volume to display at the beginning
#     slice2    Slice of the volume that ends the animation
#
# Returns:
#     str       Event string
# //

proc makeSliceNumberEvent {type N time1 time2 slice1 slice2} {
    set maxSlice ["$type-$N" sliceNumber getMaxValue]
    set str "dummy {numeric {$type-$N/Slice Number} $time1 $time2 $slice1 $slice2 0 $maxSlice "
    append str "{\"$type-$N\" sliceNumber setValue %0%; \"$type-$N\" fire}} "
    return $str
}

#//
# Function: makeTranspEvent
# -------------------------
# Generates a single classic Demo Maker event string that changes the transparency of
# a given object over a time interval.
#
# Inputs:
#     type     String specifying the object type (i.e. "Surface-View")
#     N        Integer specifying the number of the object type
#     time1    Time to start the transparency transition
#     time2    Time to end the transparency transition
#     val1     Starting transparency value (ranges from 0 - 1)
#     val2     Ending transparency value
#
# Returns:
#     str      Event string
#//

proc makeTranspEvent {type N time1 time2 val1 val2} {
    set str "dummy {numeric {$type-$N/Base Trans} $time1 $time2 $val1 $val2 0 1 "
    append str "{\"$type-$N\" baseTrans setValue %0%; \"$type-$N\" fire}} "
    return $str
}

#//
# Function: makeEventListCilium
# -----------------------------
# Generates a classic Demo Maker event string for a primary cilium visualization. Total
# length is 4 seconds. Keys (seconds):
#     00-04: Displays the smoothed, transparent rendering of the cilium so that the 
#            skeleton is visible inside
#
# Returns:
#     expr     Event string to be loaded as an internalEventList to a Demo Maker module
#     length   Duration of the movie in seconds
#//

proc makeEventListCilium {} {
    set expr [makeMaskEvent "Caption" 1 0 1]
    append expr [makeMaskEvent "Caption" 2 0 1]
    append expr [makeMaskEvent "Surface-View" 1 0 1]
    append expr [makeMaskEvent "Spatial-Graph-View" 1 0 1]
    append expr [makeTranspEvent "Surface-View" 1 0 0 0.7 0.7]
    append expr [makeCameraOrbitEvent "Camera-Orbit" 1 0 4 0 360]
    set length 4
    return [list $expr $length]
}

#//
# Function: makeEventListLyso
# ---------------------------
# Generates a classic Demo Maker event string for a short, single lysosome visualization.
# Total length is 4 seconds. Keys (seconds):
#     00-04: Displays the smoothed rendering of the lysosome and performs 360 degree
#            rotation
#
# Returns:
#     expr      Event string to be loaded as an internalEventList to a Demo Maker module
#     length    Duration of the movie in seconds
#//

proc makeEventlistLyso {} {
    set expr [makeMaskEvent "Caption" 1 0 1]
    append expr [makeMaskEvent "Caption" 2 0 1] 
    append expr [makeMaskEvent "Surface-View" 1 0 1]
    append expr [makeCameraOrbitEvent "Camera-Orbit" 1 0 4 0 360]
    set length 4
    return [list $expr $length]
}

#//
# Function: makeEventListMitoShort
# --------------------------------
# Generates a classic Demo Maker event string for a short, single mitochondrion
# visualization. Total length is 4 seconds. Keys (seconds):
#     00-04: Displays the 3D skeleton inside of transparent rendering, and performs 360
#            degree rotation
#
# Returns:
#     expr      Event string to be loaded as an internalEventList to a Demo Maker module
#     length    Duration of the movie in seconds
##//

proc makeEventListMitoShort {} {
    # Set the initial mask states. Start with only Surface View 2 (remeshed mito), Spatial 
    # Graph View 1 (3D skeleton), Caption 1 (title), and Caption 5 (sub-header) visible.
    set expr [makeMaskEvent "Bounding-Box" 1 0 0]
    append expr [makeMaskEvent "Caption" 1 0 1]
    append expr [makeMaskEvent "Caption" 2 0 0]
    append expr [makeMaskEvent "Caption" 3 0 0]
    append expr [makeMaskEvent "Caption" 4 0 0]
    append expr [makeMaskEvent "Caption" 5 0 1]
    append expr [makeMaskEvent "Ortho-Slice" 1 0 0]
    append expr [makeMaskEvent "Surface-View" 1 0 0]
    append expr [makeMaskEvent "Surface-View" 2 0 1]
    append expr [makeMaskEvent "Spatial-Graph-View" 1 0 1]

    # Make the surface 70% transparent. Rotate the surface 360 degrees
    append expr [makeTranspEvent "Surface-View" 2 0 0 0.7 0.7]
    append expr [makeCameraOrbitEvent "Camera-Orbit" 1 0 4 0 360]

    set length 4
    return [list $expr $length]
}

#//
# Function: makeEventListMitoLong
# -------------------------------
# Generates a classic Demo Maker event string for a long format, single mitochondrion
# visualization. Total length is 12 seconds. Keys (seconds):
#     00-02: Displays rendering of raw segmentation
#     04-08: Displays segmentation ortho slices inside of transparent rendering
#     08-12: Displays the 3D skeleton inside of transparent rendering, and performs 360
#            degree rotation
#
# Inputs:
#     northo    Number of slices to show in the segmentation ortho slice volume
# 
# Returns:
#     expr      Event string to be loaded as an internalEventList to a Demo Maker module
#     length    Duration of the movie in seconds
#//

proc makeEventListMitoLong {N northo} {
    # Set the initial mask states. Start with the Bounding Box, Caption 1 (main title),
    # Caption 2 (sub-header), and Surface View 1 (raw segmentation mesh) set to visible.
    set expr [makeMaskEvent [appendn "Bounding-Box-" $N] 1 0 1]
    append expr [makeMaskEvent "Caption" 1 0 1]
    append expr [makeMaskEvent "Caption" 2 0 1]
    append expr [makeMaskEvent "Caption" 3 0 0]
    append expr [makeMaskEvent "Caption" 4 0 0]
    append expr [makeMaskEvent "Caption" 5 0 0]
    append expr [makeMaskEvent [appendn "Ortho-Slice-" $N] 1 0 0]
    append expr [makeMaskEvent [appendn "Surface-View-" $N] 1 0 1]
    append expr [makeMaskEvent [appendn "Surface-View-" $N] 2 0 0]
    append expr [makeMaskEvent [appendn "Spatial-Graph-View-" $N] 1 0 0]

    # Turn off the raw segmentation mesh (Surface View 1) and turn on the remeshed version
    # (Surface View 2). Transition the surface from opaque to 70% transparent so the ortho
    # slices and skeleton can be visible.
    append expr [makeMaskEvent [appendn "Surface-View-" $N] 1 2 0]
    append expr [makeMaskEvent [appendn "Surface-View-" $N] 2 2 1]
    append expr [makeMaskEvent "Caption" 2 2 0]
    append expr [makeMaskEvent "Caption" 3 2 1]
    append expr [makeTranspEvent [appendn "Surface-View-" $N] 2 2 4 0 0.7]

    # Play through the ortho slices of the segmentation with the transparent surface
    # rendered on top. Slices go from top to bottom, then bottom to top.
    append expr [makeMaskEvent [appendn "Ortho-Slice-" $N] 1 4 1]
    append expr [makeMaskEvent "Caption" 3 4 0]
    append expr [makeMaskEvent "Caption" 4 4 1]
    append expr [makeSliceNumberEvent [appendn "Ortho-Slice-" $N] 1 4 6 $northo 0]
    append expr [makeSliceNumberEvent [appendn "Ortho-Slice-" $N] 1 6 8 0 $northo]

    # Turn off the ortho slices/bounding box and turn on the skeleton with nodes. Rotate the
    # surface 360 degrees to visualize the skeleton.
    append expr [makeMaskEvent [appendn "Bounding-Box-" $N] 1 8 0]
    append expr [makeMaskEvent [appendn "Ortho-Slice-" $N] 1 8 0]
    append expr [makeMaskEvent [appendn "Spatial-Graph-View-" $N] 1 8 1]
    append expr [makeMaskEvent "Caption" 4 8 0]
    append expr [makeMaskEvent "Caption" 5 8 1]
    append expr [makeCameraOrbitEvent "Camera-Orbit" 1 8 12 0 360]

    set length 12
    return [list $expr $length]
}

#//
# Function: remeshGeometrySurface
# --------------------
# Remeshes a loaded VRML file.
#
# Inputs:
#     surfaceIn     Name of geometry surface to remesh (e.g. "Geometry-Surface")
#     moduleName    Name to give the created module (e.g. "Remesh-Surface-1")
#     objective     Remeshes based on high regularity (=0) or best isotropic vertex placement (=1)
#     triPercent    Percentage of triangles in the mesh to retain after remeshing
#     interpolate   Smoothing is performed on the internal contours (=1) or not (=0)
#     fixContours   Fixes contours so they are not edited during smoothing(=1), or allows contour
#                   editing (=0)
#//

proc remeshGeometrySurface {surfaceIn moduleName objective triPercent interpolate fixContours} {
    create HxRemeshSurface $moduleName
    $moduleName data connect $surfaceIn
    $moduleName objective setValue $objective 
    $moduleName desiredSize setValue 2 $triPercent
    $moduleName interpolateOrigSurface setValue $interpolate
    $moduleName remeshOptions1 setValue 0 $fixContours
    $moduleName remeshOptions1 setValue 1 0
    $moduleName remesh snap
    $moduleName fire
}

#//
# Function: smoothGeometrySurface
# -------------------------------
# Smooths a previously generated geometry surface.
#
# Inputs:
#     surfaceIn    Name of geometry surface to remesh (e.g. "Geometry-Surface")
#     moduleName   Name to give the created module (e.g. "Smooth-Surface-1")
#     iterations   Number of smoothing iterations
#     lambda       Value of the shifting coefficient, which ranges from 0-1
##//
  
proc smoothGeometrySurface {surfaceIn moduleName iterations lambda} {
    create HxSurfaceSmooth $moduleName
    $moduleName data connect $surfaceIn
    $moduleName parameters setValue 0 $iterations
    $moduleName parameters setValue 1 $lambda
    $moduleName action snap
    $moduleName fire
}

#//
# Function: surface2orthoSlice
# ----------------------------
# Converts a surface to binary orthoslices. The size of the orthoslice stack is
# determined automatically.
#
# Inputs:
#     surfaceIn     Name of geometry surface to create Ortho Slices from
#     moduleName    Name to give to the created module
##//

proc surface2orthoSlice {surfaceIn moduleName} {
    global scalex scaley scalez
    set surflist [split $surfaceIn "."]
    set surfaceOut [lindex $surflist 0] 
    append surfaceOut ".scanConverted"
    create HxScanConvertSurface $moduleName
    $moduleName data connect $surfaceIn
    $moduleName field disconnect
    $moduleName fire
    set xmin [ $moduleName bbox getValue 0 ]
    set xmax [ $moduleName bbox getValue 1 ]
    set ymin [ $moduleName bbox getValue 2 ]
    set ymax [ $moduleName bbox getValue 3 ]
    set zmin [ $moduleName bbox getValue 4 ]
    set zmax [ $moduleName bbox getValue 5 ]
    set dimx [ expr round((double($xmax) / $scalex - double($xmin) / $scalex)) ]
    set dimy [ expr round((double($ymax) / $scaley - double($ymin) / $scaley)) ]
    set dimz [ expr round((double($zmax) / $scalez - double($zmin) / $scalez)) ]
    $moduleName dimensions setValues $dimx $dimy $dimz
    $moduleName action snap
    $moduleName fire
    $surfaceOut sharedColormap setValue "grayScale.am"
    $surfaceOut sharedColormap setMinMax 0 1
    $surfaceOut ImageData disconnect
    $surfaceOut fire
    $surfaceOut primary setIndex 0 0
    $surfaceOut fire
    $surfaceOut select
    $surfaceOut Voxelsize setValue "$scalex x $scaley x $scalez"
}

#//
# Function: orthoSlice2skeleton
# -----------------------------
# Creates a 3D skeleton from a stack of orthoslices using the TEASER algorithm.
#
# Inputs:
#     orthosliceIn   Name of ortho slice object to create a skeleton from
#     moduleName     Name to give to the created module
#//

proc orthoSlice2skeleton {orthoSliceIn moduleName} {
    create HxTEASAR $moduleName
    $moduleName data connect $orthoSliceIn
    $moduleName doIt snap
    $moduleName fire
}

#//
# Function: smoothSkeleton
# ------------------------
# Smooths a skeleton output from the TEASAR algorithm
#
# Inputs:
#     skeletonIn    Name of spatial graph view object to smooth
#     moduleName    Name to give to the created module
#     smooth        Smoothing coefficient (ranges from 0-1, and the greater the value,
#                   the smoother the result will be.
#     attach        Influences how much the initial positions will be retained. Should
#                   not be greater than 1.
#     iter          Number of smoothing iterations. Greater values will produce 
#                   smoother results.
#//

proc smoothSkeleton {skeletonIn moduleName smooth attach iter} {
    create HxSmoothLine $moduleName
    $moduleName lineSet connect $skeletonIn
    $moduleName coefficients setValue 0 $smooth
    $moduleName coefficients setValue 1 $attach
    $moduleName numberOfIterations setValue $iter
    $moduleName doIt snap
    $moduleName fire
}

#//
# Function: createBoundingBox
# ---------------------------
# Creates a bounding box around a specified input object.
#
# Inputs:
#     objectIn      Name of the object to create a bounding box around
#     moduleName    Name to give to the created module
#     bbwidth       Bounding box thickness. DEFAULT = 2
#     bbcolor       Bounding box color, in a comma-separated string "R,G,B". DEFAULT = 1,0.5,0
#//

proc createBoundingBox {objectIn moduleName bbwidth bbcolor} {
    create HxBoundingBox $moduleName
    $moduleName data connect $objectIn
    $moduleName lineWidth setValue $bbwidth
    set bbcolor [split $bbcolor ","]
    $moduleName options setColor 1 [lindex $bbcolor 0] [lindex $bbcolor 1] [lindex $bbcolor 2]
    $moduleName fire
}

#//
# Function: createCameraPath
# --------------------------
# Creates a camera path object, allowing for 360 degree rotation during a movie
#
# Inputs:
#     moduleName    Name to give to the created module
#//

proc createCameraPath {moduleName} {
    create HxCircularCameraPath $moduleName
    $moduleName action setOptValue 0
    $moduleName action snap
    $moduleName fire
}

#//
# Function: createCaption
# -----------------------
# Creates a caption object to display text on the screen or in a movie
#
# Inputs:
#     moduleName    Name to give to the created module
#     position      Position for the text. 0 = lower left, 1 = upper left
#     fontSize      Font size to use in the caption
#     text          String to be displayed in the caption
#//

proc createCaption {moduleName position fontSize text} {
    create HxAnnotation $moduleName
    $moduleName originPos setValue $position
    $moduleName font setFontName "Arial Unicode MS"
    $moduleName font setFontSize $fontSize
    $moduleName text setValue $text
    $moduleName fire
}

#//
# Function: createOrthoSlice
# --------------------------
# Creates an ortho slice object allowing the play through of slices
#
# Inputs:
#     volumeIn     Name of the volume/label stack to create an ortho slice object from
#     moduleName   Name to give to the created module
#//

proc createOrthoSlice {volumeIn moduleName} {
    create HxOrthoSlice $moduleName
    $moduleName data connect $volumeIn
    $moduleName colormap setValue grayScale.am
    $moduleName colormap setMinMax 0 1
    $moduleName frameSettings setValue 2 2
    $moduleName fire
    set northo [ $moduleName sliceNumber getMaxValue ]
}

#//
# Function: createSpatialGraphView
# --------------------------------
# Create a spatial graph view object, allowing, for example, the rendering 
# of a 3D line segment or skeleton.
#
# Input:
#     graphIn      Name of the graph object to render
#     moduleName   Name to give to the created module
#     nodecolor    Line node color, in a comma-separated string. DEFAULT = 1,0,0 
#     linecolor    Line color, in a comma-separated string. DEFAULT = 0.8,0.8,0.8
#     linewidth    Line thickness. DEFAULT = 3
#//

proc createSpatialGraphView {graphIn moduleName nodecolor linecolor linewidth} {
    global scalex
    echo $nodecolor
    create HxSpatialGraphView $moduleName
    $moduleName data connect $graphIn
    $moduleName nodeScaleFactor setMinMax 0 $scalex
    $moduleName nodeScaleFactor setValue $scalex
    set nodecolor [split $nodecolor ","]
    $moduleName nodeColor setColor 0 [lindex $nodecolor 0] [lindex $nodecolor 1] [lindex $nodecolor 2]
    set linecolor [split $linecolor ","]
    $moduleName segmentColor setColor 0 [lindex $linecolor 0] [lindex $linecolor 1] [lindex $linecolor 2]
    $moduleName segmentWidth setValue $linewidth
    $moduleName fire
}

#//
# Function: createSurfaceView
# ---------------------------
# Creates a surface view of a specified geometry surface.
#
# Inputs:
#     surfaceIn     Name of the geometry surface to render
#     moduleName    Name to give to the created module
#     surftrans     Alpha level (transparency) of the surface view
#     surfcolor     Surface view color, in comma-separated string "R,G,B"
#//

proc createSurfaceView {surfaceIn moduleName surftrans surfcolor} {
    create HxDisplaySurface $moduleName
    $moduleName data connect $surfaceIn
    $moduleName drawStyle setState 4 1 1 3 1 0 1
    $moduleName fire
    $moduleName baseTrans setValue $surftrans
    $moduleName colorMode setValue 5
    $moduleName fire
    set surfcolor [split $surfcolor ","]
    $moduleName colormap setDefaultColor [lindex $surfcolor 0] [lindex $surfcolor 1] [lindex $surfcolor 2]
    $moduleName fire
}

#//
# Function: setupMovieCilium
# --------------------------
# Creates the objects and surface renderings necessary to produce a movie of a primary cilium.
#
# Inputs:
#     bbwidth       Bounding box thickness.
#     bbcolor       Bounding box color, in a comma-separated string "R,G,B"
#     ciliumcolor   Cilium color, in a comma-separated string "R,G,B"
#     nodecolor     Skeleton node color
#     skelcolor     Skeleton color
#     skelwidth     Skeleton branch thickness
#
#//

proc setupMovieCilium {bbwidth bbcolor ciliumcolor nodecolor skelwidth skelcolor} {
    global base AMIRA_ROOT
    set scriptAnim [load ${AMIRA_ROOT}/share/script-objects/DemoMakerClassic.scro]
    set scriptAnim [lindex $scriptAnim 0]
    createSurfaceView "GeometrySurface.smooth" "Surface-View-1" 0 $ciliumcolor
    createSpatialGraphView "SmoothTree.spatialgraph" "Spatial-Graph-View-1" $nodecolor $skelcolor $skelwidth
    createCaption "Caption-1" 1 24 $base
    createCaption "Caption-2" 0 20 "Remeshed Surface"
    createCameraPath "Camera-Orbit-1"
    set movieParams [makeEventListCilium]
    renderMovie $scriptAnim $movieParams
}

#//
# Function: setupMovieLyso
# ------------------------
# Creates the objects and surface renderings necessary to produce a movie of a lysosome.
#
# Inputs:
#     bbwidth     Bounding box thickness.
#     bbcolor     Bounding box color, in a comma-separated string "R,G,B"
#     lysocolor   Lysosome color, in a comma-separated string "R,G,B"
#     nodecolor   Skeleton node color
#     skelcolor   Skeleton color
#     skelwidth   Skeleton branch thickness
#//

proc setupMovieLyso {bbwidth bbcolor lysocolor} {
    global base AMIRA_ROOT
    set scriptAnim [load ${AMIRA_ROOT}/share/script-objects/DemoMakerClassic.scro]
    set scriptAnim [lindex $scriptAnim 0]
    createSurfaceView "GeometrySurface" "Surface-View-1" 0 $lysocolor
    createCaption "Caption-1" 1 24 $base
    createCaption "Caption-2" 0 20 "Remeshed Surface"
    createCameraPath "Camera-Orbit-1"
    set movieParams [makeEventListLyso]
    renderMovie $scriptAnim $movieParams
}

#//
# Function: setupMovieMito
# ------------------------
# Creates the objects and surface renderings necessary to produce a movie of a mitochondrion.
#
# Inputs:
#     N            Object number
#     opts         Options array
#//

proc setupMovieMito {N} {
    global opts base AMIRA_ROOT
    set scriptAnim [load ${AMIRA_ROOT}/share/script-objects/DemoMakerClassic.scro]
    set scriptAnim [lindex $scriptAnim 0]
    createBoundingBox [appendn "GeometrySurface" $N ".smooth"] \
        [appendn "Bounding-Box-" $N "-1"] $opts(bbwidth) $opts(bbcolor)
    createSurfaceView [appendn "GeometrySurface" $N] \
        [appendn "Surface-View-" $N "-1"] 0 $opts(mitocolor)
    createSurfaceView [appendn "GeometrySurface" $N ".smooth"] \
        [appendn "Surface-View-" $N "-2"] 0 $opts(mitocolor)
    createSpatialGraphView [appendn "SmoothTree" $N ".spatialgraph"] \
        [appendn "Spatial-Graph-View-" $N "-1"] $opts(nodecolor) $opts(skelcolor) $opts(skelwidth)
    createOrthoSlice [appendn "GeometrySurface" $N ".scanConverted"] \
        [appendn "Ortho-Slice-" $N "-1"]
    set northo [ [appendn "Ortho-Slice-" $N "-1"] sliceNumber getMaxValue ]
    createCaption "Caption-1" 1 24 $base
    createCaption "Caption-2" 0 20 "Autosegmented Surface"
    createCaption "Caption-3" 0 20 "Remeshed Surface"
    createCaption "Caption-4" 0 20 "Surface Orthoslices"
    createCaption "Caption-5" 0 20 "3D Skeleton"
    createCameraPath "Camera-Orbit-1"
    if {$opts(makeMovieMitoLong)} {
        set movieParams [makeEventListMitoLong $N $northo]
    } else {
        set movieParams [makeEventListMitoShort $N]
    }
    renderMovie $scriptAnim $movieParams
}

#//
# Function: renderMovie
# ---------------------
# Sets the movie parameters, renders it, and saves it to disk
#
# Inputs:
#     scriptAnim     Module name for the imported classic demo maker module
#     movieParams    String containing the full demo maker event list
#//

proc renderMovie {scriptAnim movieParams} {
    global base
    set movieEventString [lindex $movieParams 0]
    set movieLength [lindex $movieParams 1]
    $scriptAnim setVar scroTypeDemoMaker 1
    $scriptAnim setVar "internalEventList" $movieEventString
    $scriptAnim setVar "lastStartTime" 0
    $scriptAnim setVar "lastEndTime" $movieLength
    $scriptAnim setVar "lastTimeStep" 0
    $scriptAnim setVar "loadNetwDemoMakers" {}
    $scriptAnim fire
    $scriptAnim time disconnect
    $scriptAnim time setMinMax 0 $movieLength
    $scriptAnim time setSubMinMax 0 $movieLength

    # Set the time to one and then back to zero to reset the display because Amira is stupid
    $scriptAnim time setValue 1
    $scriptAnim time setValue 0

    $scriptAnim time animationMode -once
    $scriptAnim fire
    $scriptAnim select
    $scriptAnim setPickable 1

    create HxMovieMaker "Movie-Maker-1"
    "Movie-Maker-1" time connect $scriptAnim
    "Movie-Maker-1" fire
    "Movie-Maker-1" fileFormat setValue 0
    "Movie-Maker-1" frameRate setValue 0 #Set frame rate to 24/sec
    "Movie-Maker-1" frames setValue [expr $movieLength * 24]
    "Movie-Maker-1" compressionQuality setValue 1
    "Movie-Maker-1" size setValue 2
    "Movie-Maker-1" filename setValue $base.mpg
    "Movie-Maker-1" action setState index 0
    "Movie-Maker-1" action touch 0
    "Movie-Maker-1" fire
}

#//
# Function: appendn
# -----------------
# Appends numerous input strings to one output string
#
# Inputs:
#     str_in    Input string to append to
#     args      Sub-strings to sequentially append to str_in
#
# Returns:
#     str_in    String with all sub-strings appended to it
##//

proc appendn {str_in args} {
    foreach arg $args {
        set str_in ${str_in}$arg
    }   
    return $str_in
}


proc workflow_mitochondrion {N} {
    global opts
    remeshGeometrySurface [appendn "GeometrySurface" $N] \
        [appendn "Remesh-Surface-" $N] 1 100 0 1
    smoothGeometrySurface [appendn "GeometrySurface" $N ".remeshed"] \
        [appendn "Smooth-Surface-" $N] 10 0.9
    surface2orthoSlice [appendn "GeometrySurface" $N ".smooth"] \
        [appendn "Scan-Surface-To-Volume-" $N]
    orthoSlice2skeleton [appendn "GeometrySurface" $N ".scanConverted"] \
        [appendn "Centerline-Tree-" $N]
    smoothSkeleton [appendn "GeometrySurface" $N ".Spatial-Graph"] \
        [appendn "Smooth-Line-Set-" $N] 0.7 0.2 10
    "SmoothTree.spatialgraph" setLabel [appendn "SmoothTree" $N ".spatialgraph"]
    if {$opts(makeMovieMito)} {
        setupMovieMito $N
    }
    #exportCSV "SmoothTree.spatialgraph" "Statistics-1" ${base}_skel.csv
    #exportCSV "GeometrySurface.smooth" "Statistics-2" ${base}_sva.csv
    

}

proc workflow_nucleus {} {


}

proc workflow_nucleolus {} {

}

proc workflow_plasmamembrane {} {

}

proc workflow_primarycilium {} {

}

#//
#
# MAIN
#
#//

#//
#
#
# START INPUT PARAMETRS
#
#//

# bbwidth      Bounding box thickness. DEFAULT = 2
# bbcolor      Bounding box color, in a comma-separated string "R,G,B", where each
#              value ranges from 0-1. (e.g. "1,0,0", "0.5,0.5,1") DEFAULT = 1,0.5,0
# mitocolor    Mito color, in a comma-separated string "R,G,B". DEFAULT = 0,1,0
# skelwidth    Skeleton branch thickness. DEFAULT = 3
# skelcolor    Skeleton color, in a comma-separated string. DEFAULT = 0.8,0.8,0.8
# nodecolor    Skeleton node color, in a comma-separated string. DEFAULT = 1,0,0

#File parameters
set file "mitochondrion_0047.wrl"
set path_in "../amira_test/ZT04_01_neuron_01_scaled"

# Dataset-specific parameters
set opts(scalex) 300
set opts(scaley) 300
set opts(scalez) 300

# Bounding box parameters
set opts(bbwidth) 2
set opts(bbcolor) "1,0.5,0"

# Mitochondria-specific parameters
set opts(makeMovieMito) 1
set opts(makeMovieMitoLong) 1
set opts(mitocolor) "0,1,0"
set opts(skelwidth) 3
set opts(skelcolor) "0.8,0.8,0.8"
set opts(nodecolor) "1,0,0"

# Lysosome-specific parameters
set opts(makeMovieLyso) 1
set opts(lysocolor) "1,0,0"

# Cilium-specific parameters 
set opts(makeMovieCilium) 1
set opts(ciliumcolor) "1,0.8,0.8"

#//
#
# END INPUT PARAMETERS
#
#//

set str [appendn "GeometrySurface" "0050" ".remeshed"]
echo $str

set wrlfiles [ glob $path_in/*.wrl ]
set nwrlfiles [ llength $wrlfiles ]

for {set N 0} {$N < 1} {incr N} {
    # Get basename and load file
    set fname [ lindex $wrlfiles $N ]
    set base [ file tail $fname ]
    set base [ string trimright $base ".wrl" ]
    [ load $fname ] setLabel $base

    # Get the organelle type based on the filename 
    set orglist [ split $base "_" ]
    set organelle [ lindex $orglist 0 ] 
    set number [ lindex $orglist 1 ] 
   
    # Convert VRML to Surface
    set module [ concat "Open Inventor Scene To Surface" $number ]
    echo $module
    echo $base
    create HxGeometryToSurface $module
    $module data connect $base
    $module action snap
    $module fire
    "GeometrySurface" setLabel [ appendn "GeometrySurface" $number ]

    # Run the appropriate workflow
    workflow_$organelle $number
}


# Get the organelle type based on the filename of the input VRML file
#set fnamelist [split $base "_"]
#set organelle [lindex $fnamelist 0]

# Determine workflow based on the organelle type
#if {$organelle == "mitochondrion"} {
#    remeshGeometrySurface "GeometrySurface" "Remesh-Surface-1" 1 100 0 1
#    smoothGeometrySurface "GeometrySurface.remeshed" "Smooth-Surface-1" 10 0.9
#    surface2orthoSlice "GeometrySurface.smooth" "Scan-Surface-To-Volume-1"
#    orthoSlice2skeleton "GeometrySurface.scanConverted" "Centerline-Tree-1"
#    smoothSkeleton "GeometrySurface.Spatial-Graph" "Smooth-Line-Set-1" 0.7 0.2 10
#    if {$makeMovieMito == 1} {
#        setupMovieMito $bbwidth $bbcolor $mitocolor $nodecolor $skelwidth $skelcolor
#    }
#    exportCSV "SmoothTree.spatialgraph" "Statistics-1" ${base}_skel.csv
#    exportCSV "GeometrySurface.smooth" "Statistics-2" ${base}_sva.csv
#} elseif {$organelle == "lysosome"} {
#    remeshGeometrySurface "GeometrySurface" "Remesh-Surface-1" 1 100 0 1
#    smoothGeometrySurface "GeometrySurface.remeshed" "Smooth-Surface-1" 10 0.9
#    if {$makeMovieLyso == 1} {
#        setupMovieLyso $bbwidth $bbcolor $lysocolor
#    }
#    exportCSV "GeometrySurface.smooth" "Statistics-1" ${base}_sva.csv
#} elseif {$organelle == "nucleus"} {
#    Test
#} elseif {$organelle == "nucleolus"} {
#    Test
#} elseif {$organelle == "primarycilium"} {
#    remeshGeometrySurface "GeometrySurface" "Remesh-Surface-1" 1 100 0 1
#    smoothGeometrySurface "GeometrySurface.remeshed" "Smooth-Surface-1" 10 0.7
#    surface2orthoSlice "GeometrySurface.smooth" "Scan-Surface-To-Volume-1"
#    orthoSlice2skeleton "GeometrySurface.scanConverted" "Centerline-Tree-1"
#    smoothSkeleton "GeometrySurface.Spatial-Graph" "Smooth-Line-Set-1" 0.7 0.2 10
#    if {$makeMovieCilium == 1} {
#        setupMovieCilium $bbwidth $bbcolor $ciliumcolor $nodecolor $skelwidth $skelcolor
#    }
#    exportCSV "SmoothTree.spatialgraph" "Statistics-1" ${base}_skel.csv
#}
