import adsk.core, adsk.fusion, adsk.cam, traceback

app = adsk.core.Application.get()
ui = app.userInterface
handlers = []

def drawRoundedSquare(point, sketch:adsk.fusion.Sketch, width, height, cornerRadius):
    
    centerPoint=point.geometry

    # Calculate half-dimensions
    halfWidth = width / 2
    halfHeight = height / 2

    # Define corner points based on the center point
    topLeft = adsk.core.Point3D.create(centerPoint.x - halfWidth, centerPoint.y + halfHeight, 0)
    topRight = adsk.core.Point3D.create(centerPoint.x + halfWidth, centerPoint.y + halfHeight, 0)
    bottomRight = adsk.core.Point3D.create(centerPoint.x + halfWidth, centerPoint.y - halfHeight, 0)
    bottomLeft = adsk.core.Point3D.create(centerPoint.x - halfWidth, centerPoint.y - halfHeight, 0)

    # Draw the square with lines between the corner points
    lines = sketch.sketchCurves.sketchLines
    line1 = lines.addByTwoPoints(topLeft, topRight)       # Top edge
    line2 = lines.addByTwoPoints(topRight, bottomRight)   # Right edge
    line3 = lines.addByTwoPoints(bottomRight, bottomLeft) # Bottom edge
    line4 = lines.addByTwoPoints(bottomLeft, topLeft)     # Left edge

    # Fillet each corner with the specified radius
    fillet1 = sketch.sketchCurves.sketchArcs.addFillet(line1, line1.endSketchPoint.geometry, line2, line2.startSketchPoint.geometry, cornerRadius)
    fillet2 = sketch.sketchCurves.sketchArcs.addFillet(line2, line2.endSketchPoint.geometry, line3, line3.startSketchPoint.geometry, cornerRadius)
    fillet3 = sketch.sketchCurves.sketchArcs.addFillet(line3, line3.endSketchPoint.geometry, line4, line4.startSketchPoint.geometry, cornerRadius)
    fillet4 = sketch.sketchCurves.sketchArcs.addFillet(line4, line4.endSketchPoint.geometry, line1, line1.startSketchPoint.geometry, cornerRadius)

    # Add geometric constraints
    constraints = sketch.geometricConstraints
    constraints.addPerpendicular(line1, line2)
    constraints.addPerpendicular(line2, line3)
    constraints.addPerpendicular(line3, line4)

    # Add dimensions for overall horizontal and vertical distances
    dimConstraints = sketch.sketchDimensions
    dimConstraints.addDistanceDimension(line1.startSketchPoint, line3.endSketchPoint, adsk.fusion.DimensionOrientations.AlignedDimensionOrientation, adsk.core.Point3D.create(centerPoint.x+width, centerPoint.y - height, 0))
    dimConstraints.addDistanceDimension(line2.startSketchPoint, line4.endSketchPoint, adsk.fusion.DimensionOrientations.AlignedDimensionOrientation, adsk.core.Point3D.create(centerPoint.x + width, centerPoint.y + height, 0))
    # Set a radial dimension for one fillet
    radiusDimension = dimConstraints.addRadialDimension(fillet1, adsk.core.Point3D.create(centerPoint.x + halfWidth, centerPoint.y + halfHeight, 0))
    radiusDimension.parameter.value = cornerRadius

    # Sync other fillet radii
    constraints.addEqual(fillet1,fillet2)
    constraints.addEqual(fillet1,fillet3)
    constraints.addEqual(fillet1,fillet4)

    # Add horizontal midline
    midlineStart = adsk.core.Point3D.create(centerPoint.x - halfWidth, centerPoint.y, 0)
    midlineEnd = adsk.core.Point3D.create(centerPoint.x + halfWidth, centerPoint.y, 0)
    midline = lines.addByTwoPoints(midlineStart, midlineEnd)
    midline.isConstruction=True

    # Add constraints to the midline
    constraints.addMidPoint(midline.startSketchPoint, line4)
    constraints.addMidPoint(midline.endSketchPoint, line2)
    constraints.addMidPoint(point,midline)

    #ui.messageBox('Rounded square with midline and constraints created!')


class SelectPointCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        try:
            inputs = args.command.commandInputs
            centerInput = inputs.itemById('centerPoint')
            sizeInput = inputs.itemById('sizeOption')

            # Check if sizeInput has a valid selection; default to M6 dimensions if not
            if sizeInput.selectedItem and sizeInput.selectedItem.name == 'M8':
                width, height, cornerRadius = 0.88, 0.88, 0.05
            else:
                width, height, cornerRadius = 0.67, 0.67, 0.05  # Default to M6

            point = centerInput.selection(0).entity

            # Get the active sketch
            design = app.activeProduct
            rootComp = design.rootComponent
            sketch = rootComp.sketches.item(rootComp.sketches.count - 1)  # Use the last created sketch

            drawRoundedSquare(point, sketch, width, height, cornerRadius)
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class SelectPointCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        try:
            inputs = args.command.commandInputs

            # Add a dropdown selection input for size options (M6, M8)
            sizeInput = inputs.addDropDownCommandInput('sizeOption', 'Size', adsk.core.DropDownStyles.TextListDropDownStyle)
            sizeInput.listItems.add('M6', True)  # Default to M6
            sizeInput.listItems.add('M8', False)

            # Add a selection input for the center point
            centerInput = inputs.addSelectionInput('centerPoint', 'Center Point', 'Select the center point for the rounded square')
            centerInput.setSelectionLimits(1, 1)
            centerInput.addSelectionFilter('SketchPoints')  # Allows selection of any point in the sketch

            onExecute = SelectPointCommandExecuteHandler()
            args.command.execute.add(onExecute)
            handlers.append(onExecute)
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def addCommandToUI():
    try:
        # Define command and add it to the UI in the Sketch -> Create group
        cmdDef = ui.commandDefinitions.itemById('drawRoundedSquareCmd')
        if not cmdDef:
            cmdDef = ui.commandDefinitions.addButtonDefinition('drawRoundedSquareCmd', 'Draw Rounded Square', 'Draw a rounded square centered on a selected point in a sketch', '')

        onCommandCreated = SelectPointCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        
        # Find the Sketch -> Create panel
        createPanel = ui.allToolbarPanels.itemById('SketchCreatePanel')
        createPanel.controls.addCommand(cmdDef)
        
    except:
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def run(context):
    try:
        addCommandToUI()
        ui.messageBox('Draw Rounded Square Add-In Loaded')
    except:
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    try:
        cmdDef = ui.commandDefinitions.itemById('drawRoundedSquareCmd')
        if cmdDef:
            cmdDef.deleteMe()
        
        # Remove from the Sketch -> Create panel
        createPanel = ui.allToolbarPanels.itemById('SketchCreatePanel')
        control = createPanel.controls.itemById('drawRoundedSquareCmd')
        if control:
            control.deleteMe()
        
        ui.messageBox('Draw Rounded Square Add-In Unloaded')
    except:
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
