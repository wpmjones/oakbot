![The Arborist](http://www.mayodev.com/images/arborist128.png)

# The Arborist

A custom bot for the Reddit Oak clan Discord Server. Developed by TubaKid.

If you have any questions or concerns in Discord, just type `/help` or `/help <command>` for help. 

## /player <in-game name>
List statistics, troop/spell levels, info for specified player.

## /siege <siege type>
Request siege machine of the specified type. Discord will tag all players in the clan that have the specified siege machine.

**Siege Types:**  
Wall Wrecker  
Stone Slammer  
Battle Blimp  
Siege Barracks

## /role
**/role @DiscordUser#1234 RoleName**
Adds the specified role to the specified user if they do not have it. Removes the role if they already have it.

## /warn
**/warn list**
Lists all strikes for all users. Sorted by user (alphabetically). This also provides the specific warning IDs for each warning (necessary if you want to remove a warning.

**/warn "in-game name" Reason for the warning**
Adds a strike to the specified player with the specified reason. The bot will respond with a list of all strikes for that player. No DM is sent at this time! That will be a future enhancement.

**/warn remove #**
Removes the specified warning (warning ID). You will need to do /warn list first to obtain the warning ID.

**/kick "in-game name" Reason for the kick**
Removes the player from our Google Sheet and removes the Discord role, Member.

**/ban "in-game name" Reason for the ban**
Removes the player from our Google Sheet (marked with permanent ban) and kicks the Discord user from the server.

## /unconfirmed
**/unconfirmed list**
Lists all players who have not yet confirmed the rules. If they have been in the clan for more than 2 days, you will see a boot emoji.

**/unconfirmed kick in-game name**
Moves specified player to the No Confirmation tab of our Google Sheet.

**/unconfirmed move in-game name**
Moves specified player to the Regular Members section of our Google Sheet.  This is normally done automatically when the player completes our Google Form and gets the quiz answers correct, but if they miss questions, we need a way to manually move them once the correct answers are supplied.

### Some cogs are borrowed from [EvieePy's cog examples](https://gist.github.com/EvieePy/d78c061a4798ae81be9825468fe146be)
Cogs are great.  My favorite feature is that you can load, unload, and reload cogs without stopping and restarting the entire bot.
