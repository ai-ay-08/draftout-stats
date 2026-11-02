# draftout-stats
## Introduction
Draftout is a game built within Minecraft. Players race to complete goals on a square board. The player with the most goals at the end of the game is the winner!
## Project Goal
The current Draftout statistics page at https://draftout.olavmc.com/ doesn't have enough details on the page for a specific user. You can't view a user's playstyle: what types of goals they specialize in, which goals they are the best at, and where their speed in each goal ranks compared to the global average. 

The goal of this project is to build an improved Draftout statistics page.
## MVP Scope
I'm going to build a full-stack application in React, Flask, and PostgreSQL that takes a player's Draftout username and outputs statistics such as: playstyle, goal specialty, game history, and skill relative to the global average. The application will lack a fleshed-out UI and other decorational features.
## Future Plans
- Improved UI
- UI Customization
- Improved data visualization (polygon charts)
## Tech Stack
- React (JavaScript), Flask (Python), PostgreSQL
- Data will be stored in a database
- Will access the Draftout leaderboard API (or other options if discovered)
