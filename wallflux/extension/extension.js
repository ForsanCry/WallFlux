import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import Meta from 'gi://Meta';

const WallFluxInterface = `
<node>
  <interface name="org.wallflux.Shell">
    <method name="Ping">
      <arg type="s" direction="out" name="response"/>
    </method>
    <method name="MinimizeAll">
      <arg type="as" direction="out" name="window_ids"/>
    </method>
    <method name="RestoreAll">
      <arg type="as" direction="in" name="window_ids"/>
    </method>
  </interface>
</node>`;

class WallFluxDBus {

    Ping() {
        return "pong";
    }

    MinimizeAll() {
        const minimized_ids = [];
        const workspace = global.workspace_manager.get_active_workspace();

        for (const win of workspace.list_windows()) {
            if (
                win.minimized ||
                win.get_window_type() === Meta.WindowType.DESKTOP ||
                win.get_window_type() === Meta.WindowType.DOCK
            ) continue;

            // Use stable xid/id as string identifier
            const id = String(win.get_id());
            win.minimize();
            minimized_ids.push(id);
        }

        return [minimized_ids];
    }

    RestoreAll(window_ids) {
        if (!window_ids || window_ids.length === 0) return;

        const id_set = new Set(window_ids);
        const workspace = global.workspace_manager.get_active_workspace();

        // list_windows also returns minimized ones
        const all_windows = workspace.list_windows();

        // Restore in reverse order to preserve z-order
        for (const win of all_windows.reverse()) {
            if (id_set.has(String(win.get_id()))) {
                try {
                    win.unminimize(global.get_current_time());
                } catch (_) {
                    // Window may have closed in the meantime, skip
                }
            }
        }
    }
}

let _dbusImpl = null;
let _handler  = null;
let _ownerId  = 0;

export default class WallFluxExtension {
    enable() {
        _handler = new WallFluxDBus();

        _dbusImpl = Gio.DBusExportedObject.wrapJSObject(
            WallFluxInterface,
            _handler
        );

        _dbusImpl.export(
            Gio.DBus.session,
            '/org/wallflux/Shell'
        );

        _ownerId = Gio.DBus.session.own_name(
            'org.wallflux.Shell',
            Gio.BusNameOwnerFlags.NONE,
            null,
            null
        );
    }

    disable() {
        if (_ownerId) {
            Gio.DBus.session.unown_name(_ownerId);
            _ownerId = 0;
        }
        if (_dbusImpl) {
            _dbusImpl.unexport();
            _dbusImpl = null;
        }
        _handler = null;
    }
}
