import numpy as np
import sys

def createGrid():
    # Create Initial blank grid (populate dependants)
    gridOut = [(0, [1,2,3,4,5,6,7,8,9], getMyDependants(x)) for x in range(CELLS)]
    
    # Load initial values from file.
    initialValues = loadValuesFromFile()
    for v in initialValues:
        # Prime the cell for update, i.e. set its only possibly value. 
        gridOut[v[0]] = (0, [v[1]], gridOut[v[0]][2])
    
    # Now apply these initial values.
    updateGrid(gridOut)

    return gridOut 

def loadValuesFromFile():
    
    with open("grid.txt") as f:
        content = f.read().replace('\n', '')
    f.close()

    values = []
    for i, c in enumerate(content):
        if c != '-':
            values.append((i, int(c)))

    return values


def drawGrid(gridIn):
    vals = [x[0] for x in gridIn]
    print(np.array(vals).reshape((9,9))) 

def getCellIndex(rowIn, colIn):
    return (rowIn * 9) + colIn

def updateGrid(gridIn):

    identifyHiddenSingle(gridIn, getRowCells)
    identifyHiddenSingle(gridIn, getColCells)
    identifyHiddenSingle(gridIn, getMiniBoxCells)

    updateCount = 0
    #  Can we solve any cells?
    for i, cell in enumerate(gridIn):
        # We can solve the cell if it's not been set and has 1 possibility left
        if (len(cell[1]) == 1 and cell[0] == 0):
            solveCell(gridIn, i, cell)        
            updateCount = updateCount +  1
    
    return updateCount

def solveCell(gridIn, indexIn, cellIn):
     # Cell is solved., i.e. set it's value, empty its possibility list. It's dependants are unchanged
    newVal = cellIn[1][0]
    gridIn[indexIn] = (newVal, [], cellIn[2])

    # We now need to inform its dependants, so they can remove the value from their list of possible values.
    for dependant in cellIn[2]:
        # Simply remove the value just set from the dependant (as it can't be this value)
        gridIn[dependant] = (gridIn[dependant][0], [x for x in gridIn[dependant][1] if x != newVal] ,gridIn[dependant][2] )

def getRowCells(rowRefIn):
    return [x for x in range(rowRefIn * 9, (rowRefIn * 9) + 9)]

def getColCells(colRefIn):
    return [x for x in range(colRefIn, (colRefIn + 73), 9)]

def getMiniBoxCells(mbRefIn):
    return  MINI_BOX_CELLS[mbRefIn]   

def getRow(myCellRef):
    return int(myCellRef / 9)

def getCol(myCellRef):
    return int(myCellRef % 9)

def getMyRowPals(myCellRef):
    myRow = getRow(myCellRef)
    return [x for x in getRowCells(myRow) if x != myCellRef]
    
def getMyColPals(myCellRef):
    myCol = getCol(myCellRef)
    return [x for x in getColCells(myCol) if x != myCellRef]

def getMyMiniBoxPals(myCellRef):
    myMiniBox = getMyMiniBox(myCellRef)
    return [x for x in MINI_BOX_CELLS[myMiniBox] if x != myCellRef]

def getMyMiniBox(myCellRef):
    myRow = getRow(myCellRef)
    myCol = getCol(myCellRef)
    if myRow in [0,1,2]:
        a = {0,1,2}
    elif myRow in [3,4,5]:
        a = {3,4,5}
    elif myRow in [6,7,8]:
        a = {6,7,8}
    else:
        raise Exception("getMyMiniBox Error") 

    if myCol in [0,1,2]:
        b = {0,3,6}
    elif myCol in [3,4,5]:
        b = {1,4,7}
    elif myCol in [6,7,8]:
        b = {2,5,8}
    else:
        raise Exception("getMyMiniBox Error")

    return list(a.intersection(b))[0]

def getMyMiniBoxPals(myCellRef):
    myMiniBox = getMyMiniBox(myCellRef)
    return [x for x in MINI_BOX_CELLS[myMiniBox] if x != myCellRef]

def getMyDependants(myCellRef):
    return list(set(getMyColPals(myCellRef) + getMyRowPals(myCellRef) + getMyMiniBoxPals(myCellRef)))

def getBlockValues(gridIn,blockIn):
    return [gridIn[x][0] for x in blockIn if gridIn[x][0] != 0 ]

def identifyHiddenSingle(gridIn, blockGenerator):
    # good comment needed. but this is in a block of cells
    # Note: Block is a row, col or mini box
    for i in range(9):
        block = blockGenerator(i)
       
        blockValues = getBlockValues(gridIn, block)
        
        blockPossibles = [x for x in range(1,10) if x not in blockValues]

        for i in blockPossibles:       
            count = 0
            for j in block:
                if i in gridIn[j][1]:
                    specialCandidate = j
                    count = count + 1
                    if count > 1:
                        break
            if count == 1:
                gridIn[specialCandidate] = (0, [i], gridIn[specialCandidate][2])
    return []

def numOutstandingCells(gridIn):
    return len([x for x in gridIn if x[0] == 0])

#============================================
# Globals / Constants
#============================================
CELLS = 9 * 9
MINI_BOX_CELLS = [ [0,1,2,9,10,11,18,19,20], 
                    [3,4,5,12,13,14,21,22,23],
                    [6,7,8,15,16,17,24,25,26],
                    [27,28,29,36,37,38,45,46,47],
                    [30,31,32,39,40,41,48,49,50],
                    [33,34,35,42,43,44,51,52,53],
                    [54,55,56,63,64,65,72,73,74],
                    [57,58,59,66,67,68,75,76,77],
                    [60,61,62,69,70,71,78,79,80]
                     ]

#============================================
# Main Program
#============================================

try:
     
    sudukoGrid = createGrid()    
    drawGrid(sudukoGrid)

    input("Press Enter to solve...")

    iteration = 1
    while (updateGrid(sudukoGrid)):
        drawGrid(sudukoGrid)
        print("After Iteration ", iteration, " . Outstanding Cells = ", numOutstandingCells(sudukoGrid))
        iteration = iteration + 1

# To DO
# - Need a count of how many cells are left


except Exception as e:
    print("Aborting..../n", e)
