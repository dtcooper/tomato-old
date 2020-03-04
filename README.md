# Tomato Radio Automation

<img src="https://raw.github.com/dtcooper/tomato/master/docs/banner.png" width="200">

Client and server code for Tomato Radio Automation software. Simple, easy to use,
and hard to screw up Playout software written very specifically
for [Burning Man Information Radio](https://bmir.org/)'s use case (BMIR).

## Development

Tomato is in *active development* right now. So expect things to change and break.
Often. See the [TODO list](/docs/TODO.md) for things left to implement.

## Client

Cross-platform (macOS/Windows/Linux), native Desktop application.

<img src="https://raw.github.com/dtcooper/tomato/master/docs/client-screenshot-preview3.png">

The client utilizes the following,

* [CEF Python](https://github.com/cztomczak/cefpython/), ie Python's bindings to
  the [Chromium Embedded Framework](https://bitbucket.org/chromiumembedded/cef).
* [Jinja2](https://palletsprojects.com/p/jinja/) for HTML templates.
* [NES.css](https://nostalgic-css.github.io/NES.css/) as a novel CSS library for
  retro UI components.
* [wavesurfer.js](https://wavesurfer-js.org/) to play audio assets and render
  seekable audio waveforms in the UI.
* [jQuery](https://jquery.com/) for UI interactions. _Don't judge me!_
* [PyInstaller](https://pyinstaller.readthedocs.io/en/stable/) to build
  distributable, cross-platform binaries.

## Server

<img src="https://raw.github.com/dtcooper/tomato/master/docs/server-screenshot-preview1.png">

Server is a straightforward [Django](https://www.djangoproject.com/) app, taking full
advance of Django's admin interface with
[Constance](https://github.com/jazzband/django-constance) as a configuration editor.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file
for details.

