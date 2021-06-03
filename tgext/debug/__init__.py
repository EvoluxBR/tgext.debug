import logging
import threading
import time
import weakref

from tg import config, request, app_globals

try:
    # Verify that we have hooks with disconnect feature,
    # which is only available since TG2.3.5, otherwise
    # use app_config to register/disconnect hooks.
    from tg import hooks as tg_hooks
    if not hasattr(tg_hooks, 'disconnect'):
        tg_hooks = None
except ImportError:
    tg_hooks = None

try:
    # TG >= 2.4
    from tg import ApplicationConfigurator
except ImportError:
    # TG < 2.4
    class ApplicationConfigurator:
        pass

try:
    from sqlalchemy import event
    from sqlalchemy.engine.base import Engine
    has_sqla = True
except ImportError:
    has_sqla = False

log = logging.getLogger('tgext.debug')
lock = threading.Lock()


class Debug():
    def __init__(self, app_config, debugger):
        self.app_config = app_config
        self.debugger = debugger

    def _register_hook(self, hook_name, handler):
        if hook_name == 'startup':
            handler()
            return

        if tg_hooks is None:
            # 2.1+
            self.app_config.register_hook(hook_name, handler)
        elif hasattr(tg_hooks, 'wrap_controller'):
            # 2.3+
            if hook_name == 'controller_wrapper':
                def _accept_decoration(decoration, controller):
                    return handler(controller)
                tg_hooks.wrap_controller(_accept_decoration)
            else:
                tg_hooks.register(hook_name, handler)
        else:
            # 2.4+
            if hook_name == 'controller_wrapper':
                from tg import ApplicationConfigurator
                dispatch = ApplicationConfigurator.current().get_component('dispatch')
                if dispatch is None:
                    raise RuntimeError(
                        'TurboGears application configured without dispatching')
                dispatch.register_controller_wrapper(handler)
            else:
                tg_hooks.register(hook_name, handler)

    def _hook_sqlalchemy(self):

        def _before_cursor_execute(conn, cursor, stmt, params, context, execmany):
            setattr(conn, '_tgextdebug_start_timer', time.time())

        def _after_cursor_execute(conn, cursor, stmt, params, context, execmany):

            stop_timer = time.time()
            try:
                req = request._current_obj()
            except:
                req = None

            if req is not None:
                with lock:
                    engines = getattr(
                        app_globals, '_tgextdebug_sqla_engines', {})
                    engines[id(conn.engine)] = weakref.ref(conn.engine)
                    setattr(app_globals, '_tgextdebug_sqla_engines', engines)
                    queries = getattr(req, '_tgextdebug_sqla_queries', [])
                    queries.append({
                        'engine_id': id(conn.engine),
                        'duration': (stop_timer - conn._tgextdebug_start_timer) * 1000,
                        'statement': stmt,
                        'parameters': params,
                        'context': context
                    })
                    req._tgextdebug_sqla_queries = queries

            delattr(conn, '_tgextdebug_start_timer')

        def _enable_sqlalchemy():
            log.info('Enabling debug SQLAlchemy queries')
            event.listen(Engine, "before_cursor_execute",
                         _before_cursor_execute)
            event.listen(Engine, "after_cursor_execute", _after_cursor_execute)

        self._register_hook("startup", _enable_sqlalchemy)

    def _disconnect_hook(self, hook_name, handler):
        if tg_hooks is None:
            self.app_config.hooks[hook_name].remove(handler)
        else:
            tg_hooks.disconnect(hook_name, handler)

    def _call_debug(self, response):
        debug_handler = getattr(self.debugger, 'handler', None)

        if debug_handler:
            queries = []
            if hasattr(request, '_tgextdebug_sqla_queries'):
                queries = getattr(request, '_tgextdebug_sqla_queries')
                # delattr(request, '_tgextdebug_sqla_queries')
            try:
                log.debug("%s %r QUERIES=%s" %
                          (request.method, request.url, len(queries)))
                debug_handler(request, queries)
            except:
                log.exception("Error while call debug_handler")

    def __call__(self, configurator=None, conf=None):

        # # get from config
        # enable_sqla = True

        if has_sqla:
            self._hook_sqlalchemy()

        self._register_hook('after_render', self._call_debug)


def enable_debug(app_config, debugger):
    if isinstance(app_config, ApplicationConfigurator):
        tg_hooks.register('initialized_config', Debug(app_config, debugger))
    else:
        if tg_hooks is None:
            app_config.register_hook('startup', Debug(app_config, debugger))
        else:
            tg_hooks.register('startup', Debug(app_config, debugger))
