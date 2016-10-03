# MPD skill

This is a simple [Mycroft](https://mycroft.ai) skill for connecting to and controlling media players via the MPD protocol.

## Installation

Enter the mycroft virtualenv amd go to the third party skill directory
```
  workon mycroft
  cd [THIRD PARTY SKILL DIRECTORY]
```

Clone the git repository
```
  git clone https://github.com/forslund/mpd_skill.git
```

Install prerequisites into the mycroft environment
```
  pip install -r mpd_skill/requirements.txt
```

## Configuration

By default the mpd skill tries to connect to localhost on port 6600 if this is not desirable edit the mycroft.ini file

```
  [MPDSkill]
  mpd_url=YOUR_URL
  mpd_port=YOUR_PORT
```


## What it does

The skill retrievs all listable albums, artists and genres and can play each of these.

"Hey Mycroft, play Beastie Boys" will queue up all tracks by *Beastie Boys* and play them.

"Hey Mycroft, play Hello Nasty" will only queue up the album *Hello Nasty*

"Hey Mycroft, play some Rock music" will queue up all songs tagged as *Rock*.


Also pausing and resuming is possible along with stop and skipping tracks with commands like 

- next track
- pause
- stop
