# fwait

fwait is a CLI utility to watch files for changes (currently creation, deletion, modification, and movement) and react with a command. It relies on gamin, which uses Linux's inotify and the BSDs' kqueue, so it *should* run on everything except Windows, although I've only tested Linux.

## Options

    usage: fwait [-h] [-c COMMAND] [-I REPLACE] [-o] file [file ...]
    
    Executes a command when files change.
    
    positional arguments:
      file                  file or directory to watch
    
    optional arguments:
      -h, --help            show this help message and exit
      -c COMMAND, --command COMMAND
                            command to execute
      -I REPLACE, --replace REPLACE
                            substitute string with filename (like xargs)
      -o, --once            exit after first event

## Examples

Block until a file is changed and immediately exit.

    fwait -o /var/run/daemon.pid

Send a message whenever the file is changed.

	fwait /etc/passwd -c 'echo passwd changed! | mail -s alert root@localhost'

Rebuild when source file is changed (zsh globbing shown).

	fwait **/*.c -c make

Recompile/minify when a source LESS file is changed.

	fwait *.less -I FILE -c 'lessc -x FILE > FILE.css'

## Bugs

There're plenty of them. This is mostly a neat toy born of boredom and curiosity.
It's a pretty Unix-y tool, and could be quite useful if it were done well enough. We need:

- Fewer bugs
- More granularity: Only match writes, deletes, etc.
- Pattern matching: To watch newly created files.

## Authors, Contributing

[Please read: A personal appeal from fwait founder Jacob Courtneay](https://github.com/sporkexec/fwait)
