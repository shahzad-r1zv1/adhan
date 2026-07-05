# Raspberry Pi Adhan Clock
This projects uses a python script which automatically calculates [adhan](https://en.wikipedia.org/wiki/Adhan) times every day and plays all five adhans at their scheduled time using cron. 

## Prerequisites
1. Raspberry Pi running Raspberry Pi OS
  1. I would stay away from Raspberry Pi zero esp if you're new to this stuff since it doesn't come with a built in audio out port.
  2. Also, if you haven't worked with raspberry pi before, I would highly recommend using [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash Raspberry Pi OS onto your SD card and get it up and running.
2. Speakers
3. Auxiliary audio cable
4. An audio player. `omxplayer` was used historically, but it is no longer available on current Raspberry Pi OS releases (Bullseye and later) since it depended on the legacy VideoCore firmware. `playAzaan.sh` will automatically use `omxplayer` if present, otherwise it falls back to `mpg123`, `mpv`, `ffplay`, or `vlc`, in that order. Install one with, for example:
  * `$ sudo apt-get install mpg123`

## Instructions
1. Install git: Go to raspberry pi terminal (command line interface) and install `git`
  * `$ sudo apt-get install git`
2. Clone repo: Clone this repository on your raspberry pi in your `home` directory. (Tip: run `$ cd ~` to go to your home directory)
  * `$ git clone <get repo clone url from github and put it here>`
  * After doing that you should see an `adhan` directory in your `home` directory.
3. Install Python dependencies:
  * `$ pip3 install -r ~/adhan/requirements.txt`

## Run it for the first time
Run this command:

```bash
$ /home/pi/adhan/updateAzaanTimers.py --lat <YOUR_LAT> --lng <YOUR_LNG> --method <METHOD>
```

Replace the arguments above with your location information and calculation method:
* Set the latitude and longitude so it can calculate accurate prayer times for that location.
* Set adhan time [calculation method](http://praytimes.org/manual#Set_Calculation_Method).

If everythig worked, your output will look something like this:
```
20 60 Egypt 0 0
05:51
11:52
14:11
16:30
17:53
51 5 * * * /home/pi/adhan/playAzaan.sh /home/pi/adhan/Adhan-fajr.mp3 0 # rpiAdhanClockJob
52 11 * * * /home/pi/adhan/playAzaan.sh /home/pi/adhan/Adhan-Madinah.mp3 0 # rpiAdhanClockJob
11 14 * * * /home/pi/adhan/playAzaan.sh /home/pi/adhan/Adhan-Madinah.mp3 0 # rpiAdhanClockJob
30 16 * * * /home/pi/adhan/playAzaan.sh /home/pi/adhan/Adhan-Madinah.mp3 0 # rpiAdhanClockJob
53 17 * * * /home/pi/adhan/playAzaan.sh /home/pi/adhan/Adhan-Madinah.mp3 0 # rpiAdhanClockJob
0 1 * * * /home/pi/adhan/updateAzaanTimers.py >> /home/pi/adhan/adhan.log 2>&1 # rpiAdhanClockJob
@monthly truncate -s 0 /home/pi/adhan/adhan.log 2>&1 # rpiAdhanClockJob
Script execution finished at: 2017-01-06 21:22:31.512667
```

If you look at the last few lines, you'll see that 5 adhan times have been scheduled. Then there is another line at the end which makes sure that at 1am every day the same script will run and calculate adhan times for that day. And lastly, there is a line to clear logs on a monthly basis so that your log file doesn't grow too big.

Note that for later runs you do not have to supply any arguments as they are saved in `/home/pi/adhan/.settings`.

The `.settings` file is a single comma-separated line with the fields (in order):
`lat,lng,method,fajr_azaan_vol,azaan_vol,cron_user,fajr_audio,dhuhr_audio,asr_audio,maghrib_audio,isha_audio`.
It is generated and updated automatically by `updateAzaanTimers.py`; you normally don't need to edit it by hand.

VOILA! You're done!! Plug in your speakers and enjoy!

Please see the [manual](http://praytimes.org/manual) for advanced configuration instructions. 

There are 2 additional arguments that are optional, you can set them in the first run or
further runs: `--fajr-azaan-volume` and `azaan-volume`. You can control the volume of the Azaan
by supplying numbers in millibels. To get more information on how to select the values, run the command with `-h`.

## Additional configuration options

* `--<prayer>-audio`: Choose which mp3 file to play for a specific prayer, e.g. `--dhuhr-audio Adhan-Makkah.mp3`. By default fajr uses `Adhan-fajr.mp3` and the other four prayers use `Adhan-Madinah.mp3`; several other adhan recordings are bundled in this repo (`Adhan-Makkah.mp3`, `Adhan-Turkish.mp3`, `Adhan-Mishary-Rashid-Al-Afasy.mp3`, etc.) to choose from.
* Random audio: unless a prayer's audio has been explicitly set (via `--<prayer>-audio` or a previously saved customization), `updateAzaanTimers.py` randomly picks a different bundled adhan mp3 for dhuhr, asr, maghrib and isha each time it runs, to mix up which adhan is played. Files with "Dua" in the name and fajr's own audio are never selected this way. Fajr's audio is never randomized. Pass `--disable-random-audio` to always use the configured/default audio instead.
* `--cron-user`: The OS user under which to install the cron jobs. Defaults to the user currently running the script, so this only needs to be set if you want to install the jobs for a different user.
* `--dry-run`: Print out the prayer times and cron jobs that would be installed without actually writing them to crontab. Useful for testing changes safely.

## Configuring custom actions before/after adhan

Sometimes it is needed to run custom commands either before, after or before
and after playing adhan. For example, if you have
[Quran playing continuously](https://github.com/LintangWisesa/RPi_QuranSpeaker),
you would want to pause and resume the playback. Another example, is to set your
status on a social network, or a calendar, to block/unblock the Internet
using [pi.hole rules](https://docs.pi-hole.net/), ... etc.

You can easily do this by adding scripts in the following directories:
- `before-hooks.d`: Scripts to run before adhan playback
- `after-hooks.d`: Scripts to run after adhan playback

### Example:
To pause/resume Quran playback if using the
[RPi_QuranSpeaker](https://github.com/LintangWisesa/RPi_QuranSpeaker) project, place
the following in 2 new files under the above 2 directories:

```bash
# before-hooks.d/01-pause-quran-speaker.sh
#!/usr/bin/env bash
/home/pi/RPi_QuranSpeaker/pauser.py pause
```

```bash
# after-hooks.d/01-resume-quran-speaker.sh
#!/usr/bin/env bash
/home/pi/RPi_QuranSpeaker/pauser.py resume
```

Do not forget to make the scripts executable:
```bash
chmod u+x ./before-hooks.d/01-pause-quran-speaker.sh
chmod u+x ./after-hooks.d/01-resume-quran-speaker.sh
```

## Tips:
1. You can see your currently scheduled jobs by running `crontab -l`
2. The output of the job that runs at 1am every night is being captured in `/home/pi/adhan/adhan.log`. This way you can keep track of all successful runs and any potential issues. This file will be truncated at midnight on the first day of each month. To view the output type `$ cat /home/pi/adhan/adhan.log`

## Development

* Install test dependencies: `pip3 install -r requirements.txt pytest flake8`
* Run tests: `pytest tests/`
* Run lint: `flake8 .`

## Credits
I have made modifications / bug fixes but I've used the following as starting point:
* Python code to calculate adhan times: http://praytimes.org/code/ 
* Basic code to turn the above into an adhan clock: http://randomconsultant.blogspot.co.uk/2013/07/turn-your-raspberry-pi-into-azaanprayer.html
* Cron scheduler: https://pypi.python.org/pypi/python-crontab/ 
