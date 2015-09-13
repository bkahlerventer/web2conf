# Introduction #

web2conf is a simple conferencing system originally built for PyCon 2009 in less than 4 weeks.   It was successfully used for PyCon 2009 and, with a few updates for PyCon 2010.

It was originally hosted on [Launchpad](https://launchpad.net/web2conf), but has been moved here to take advantage of mercurial, and the code review system in place.

The primary parts of web2py used in [PyCon](http://use.pycon.org/2010/register) are user registration, financial management and reporting.

The Conference site scheduling, talk review, and sprint areas were managed by [pycon-tech](https://pycon.coderanger.net/), a django 0.9 application. **UPDATE**: this is now supported by web2conf

The web2py version of PyCon 2010 is mirrored here in the pycon2010 repository, complete with the copy of web2py deployed (which is somewhat old in the pycon2010 mirror).

~~Moving forward, web2conf will focus on implementing conference site components in an architecture specifically designed to be (as much as possible) web-framework independent (but note: I will only be considering Python-based frameworks)~~ **NOTE**: only web2py will be supported by this project.