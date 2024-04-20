#Requires AutoHotkey v2.0

counter := 1

Sleep(10000)

Loop 1000 {
    ; Start New Game
    MouseClick("left", 1000, 420)
    Sleep(500)
    
    ; Generate a unique save game ID
    currentTimestamp := A_TickCount
    saveGameID := "auto" . counter . "_" . currentTimestamp
    counter++
    
    ; Input the save game ID
    SendInput(saveGameID)
    Sleep(100)
    
    ; Hit enter and '1' to progress
    SendInput("{Enter}")
    Sleep(100)
    SendInput("1")
    Sleep(100)
    SendInput("2")
    Sleep(100)
    SendInput("2")
    Sleep(100)
    SendInput("2")
    Sleep(100)
    SendInput("2")
    Sleep(2000)
    SendInput("G")
    
    ; Wait for the sector to generate (adjust sleep duration as needed)
    Sleep(20000) ; Wait for 20 seconds
    
    ; Open the game menu by pressing 'esc'
    SendInput("{Esc}")
    Sleep(500)
    
    ; Exit the game (using mouse)
    ; You'll need to replace the coordinates with the actual positions of the exit button
    MouseClick("left", 700, 600)
    Sleep(500)
    SendInput("{Enter}")
    Sleep(3000)
}

ExitApp
