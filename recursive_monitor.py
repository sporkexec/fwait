import os
import sys
import gamin
import logging

_log = logging.getLogger('RecursiveMonitor')

try:
	from functools import partial # Python >= 2.5
	_log.debug('Using standard >=2.5 partial functions.')
except ImportError, e:
	_log.debug('Using fallback partial functions.')
	def partial(fun, **kwargs):
		def wrapper(*args_called, **kwargs_called):
			kw = dict(kwargs)
			kw.update(kwargs_called)
			return fun(*args_called, **kw)
		return wrapper

class RecursiveMonitor(object):
	"""
	Provides a straightforward interface to recursively monitor folders.
	Implemented as a thin wrapper around gamin, which is old and creaky
	but supported across Linux and *BSD.
	"""

	_gamin_monitor = None
	_user_callback = None
	_follow_symlinks = False
	_ignore_directories = True
	_watched_directories = []

	def __init__(self, folder_paths, callback, follow_symlinks=False, call=True, ignore_directories=True):
		"""
		Initiates a recursive monitor.
		folder_paths - String containing a folder path or an iterable
			containing any number of such strings. If a directory
			is not supplied, IOError will be raised.
		callback - A callable(abspath, event) which will be called with
			two arguments, the first being the absolute path of the
			modified file or folder, and the second being response
			codes as defined by the gamin module.
		follow_symlinks - Whether to acknowledge the existence of any
			symbolic links in the tree, including the top folder.
		call - Whether to invoke the __call__ method immediately upon
			initialization. This will usually be the desired
			behavior, as there is currently no way to suspend the
			monitor loop once started.
		ignore_directories - Whether any events on folders should be
			reported to the callback. They are not by default, by
			the rationale that if you want to deal with folders,
			it's likely not a very large additional step to
			implement this class's functionality. Note that this
			has no effect on whether files within directories are
			monitored. They are always monitored.
		"""

		self._loop = True
		self._gamin_monitor = gamin.WatchMonitor()
		self._user_callback = callback
		self._ignore_directories = ignore_directories
		if hasattr(folder_paths, '__iter__'):
			for path in folder_paths:
				self._initdir(path)
		else:
			self._initdir(folder_paths)

		if call:
			self.__call__()

	def __call__(self):
		while self._loop:
			self._gamin_monitor.handle_one_event()

	def _callback(self, path, event, basedir=''):
		codes = {7:'acknowledge',
			1:'changed',
			5:'created',
			2:'deleted',
			8:'exists',
			9:'endexists',
			6:'moved',
			3:'startexec',
			4:'endexec',}
		path = os.path.join(basedir, path)
		path = os.path.abspath(path)

		_log.debug('%s, %s' % (codes[event], path))

		if os.path.isdir(path):
			if event in (gamin.GAMCreated, gamin.GAMExists, gamin.GAMChanged):
				self._watch_directory(path)
			elif event in (gamin.GAMDeleted,):
				self._gamin_monitor.stop_watch(path)
				self._watched_directories.remove(path)
			elif gamin.GAMMoved == event:
				pass

			if self._ignore_directories:
				return

		self._user_callback(path, event)

	def _initdir(self, path):
		"""
		Recursively start listening on directory taking into acount symlinks.
		There will be a slight performance hit on Python < 2.6 if there are
		many symlinks because we have to take an exception for every one.
		TODO: Investigate performance. When would it be faster to not try
		follow_symlinks (>= 2.6 only) and use the same code for all versions,
		avoiding the exception but introducing slower code on newer versions?
		"""
		if not os.path.isdir(path):
			_log.error('%s is not a directory.' % repr(path))

		try:
			for dirname, childdirs, childfiles in os.walk(top=path,
				followlinks=self._follow_symlinks):
					self._watch_directory(dirname)
		except TypeError, e:
			for dirname, childdirs, childfiles in os.walk(top=path):
				self._watch_directory(dirname)
				if self._follow_symlinks:
					for dir in filter(os.path.islink, childdirs):
						self._initdir(os.path.join(dirname, dir))

	def _watch_directory(self, dirname):
			dirname = os.path.abspath(dirname)
			if not self._follow_symlinks and os.path.islink(dirname):
				return
			if dirname in self._watched_directories:
				return
			if not os.path.isdir(dirname):
				return

			_log.debug('Watching %s' % (dirname,))
			self._watched_directories.append(dirname)
			callback = partial(self._callback, basedir=dirname)
			self._gamin_monitor.watch_directory(dirname, callback)

	def quit(self, *_):
		self._gamin_monitor.disconnect()
		self._loop = False

