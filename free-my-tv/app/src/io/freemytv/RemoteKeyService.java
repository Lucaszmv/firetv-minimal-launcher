package io.freemytv;

import android.accessibilityservice.AccessibilityService;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.view.KeyEvent;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

/**
 * Sees the remote's keys before any app does, so the app buttons work from inside Netflix, Disney and the rest. The
 * system waits for it on every key (up to half a second), so it runs in a process of its own and does next to nothing.
 * Fire TV: when the stock launcher's window reaches the front (the Home button always lands there), brings Free My
 * TV's home screen back over it (Home Trap; toggle is the service switch, and "Original" never traps).
 */
public class RemoteKeyService extends AccessibilityService {
    private static long lastTrap;
    private static volatile String lastLauncherActivity;   // real Activity on top (from WINDOW_STATE_CHANGED), not a View class
    private android.os.Handler handler;
    private int launcherTicks;
    private volatile boolean fmtvForeground;   // confirmation ticks before the poll fires (gives the window event time to say which screen it is)
    private BroadcastReceiver screenReceiver;
    private android.hardware.display.DisplayManager.DisplayListener displayListener;
    private volatile boolean wasDreamingOrScreenOff;

    @Override protected boolean onKeyEvent(KeyEvent event) {
        // Ao apertar o botao Power ou Sleep, finaliza imediatamente o app aberto e vai para a Home
        if (event.getKeyCode() == KeyEvent.KEYCODE_POWER || event.getKeyCode() == KeyEvent.KEYCODE_SLEEP) {
            wasDreamingOrScreenOff = true;
            if (event.getAction() == KeyEvent.ACTION_DOWN) {
                dismissCurrentAppAndGoHome();
            }
            return false;
        }

        // Fire TV: when the trap is on, Home is ours — consume the key and show ours now (no launcher flash).
        if (event.getAction() == KeyEvent.ACTION_DOWN && event.getKeyCode() == KeyEvent.KEYCODE_HOME
                && trapOn()) {
            long now = System.currentTimeMillis();
            if (now - lastTrap >= 120) {
                lastTrap = now;
                tryLaunch();
            }
            return true;
        }
        return RemoteKeys.onKey(this, event);
    }

    @Override public void onAccessibilityEvent(AccessibilityEvent event) {
        CharSequence p = event.getPackageName();
        if (event.getEventType() != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED || p == null) return;
        CharSequence c = event.getClassName();
        String cls = c == null ? "" : c.toString();
        String pkg = p.toString();

        if ("io.freemytv".equals(pkg)) {
            fmtvForeground = true;
            if (cls.contains("Screensaver")) {
                wasDreamingOrScreenOff = true;
            } else {
                wasDreamingOrScreenOff = false;
            }
            return;
        }

        // Se for janela de screensaver de sistema
        if (cls.contains("DreamActivity") || pkg.contains("screensaver") || pkg.contains("bueller.photos")) {
            wasDreamingOrScreenOff = true;
            fmtvForeground = false;
            return;
        }

        // Se estava em repouso/screensaver e qualquer outro app (ou a home nativa) aparecer, forçar FreeMyTV
        if (wasDreamingOrScreenOff && trapOn()) {
            wasDreamingOrScreenOff = false;
            dismissCurrentAppAndGoHome();
            return;
        }

        fmtvForeground = false;
        if (!"com.amazon.tv.launcher".contentEquals(p) || !Prefs.homeTrap() || !trapOn()) return;
        lastLauncherActivity = cls;
        if (cls.length() > 0 && !cls.contains("HomeActivity")) return;
        long now = System.currentTimeMillis();
        if (now - lastTrap < 120) return;
        lastTrap = now;
        tryLaunch();
    }

    private void dismissCurrentAppAndGoHome() {
        String activePkg = null;
        AccessibilityNodeInfo root = getRootInActiveWindow();
        try {
            if (root != null) {
                CharSequence p = root.getPackageName();
                if (p != null) activePkg = p.toString();
            }
        } catch (Throwable ignored) {
        } finally {
            recycle(root);
        }

        // Abre a nossa Home (FreeMyTV) diretamente
        tryLaunch();

        // Mata os processos em background
        final String targetPkg = activePkg;
        killBackgroundApps(targetPkg);
        if (handler != null) {
            handler.postDelayed(() -> killBackgroundApps(targetPkg), 250);
            handler.postDelayed(() -> killBackgroundApps(targetPkg), 600);
        }
    }

    private void killBackgroundApps(String activePkg) {
        try {
            android.app.ActivityManager am = (android.app.ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
            if (am == null) return;
            if (activePkg != null && !"io.freemytv".equals(activePkg) && !"com.amazon.tv.launcher".equals(activePkg)) {
                am.killBackgroundProcesses(activePkg);
            }
            java.util.List<android.app.ActivityManager.RunningAppProcessInfo> procs = am.getRunningAppProcesses();
            if (procs != null) {
                for (android.app.ActivityManager.RunningAppProcessInfo pInfo : procs) {
                    if (pInfo.pkgList != null) {
                        for (String pkg : pInfo.pkgList) {
                            if (!"io.freemytv".equals(pkg)
                                    && !pkg.startsWith("com.amazon.")
                                    && !"android".equals(pkg)
                                    && !"com.android.systemui".equals(pkg)) {
                                am.killBackgroundProcesses(pkg);
                            }
                        }
                    }
                }
            }
        } catch (Throwable ignored) {}
    }

    private void tryLaunch() {
        try {
            // NUNCA chamar performGlobalAction(GLOBAL_ACTION_HOME) aqui, pois no Fire OS ele invoca a home original da Amazon
            startActivity(new Intent(Intent.ACTION_MAIN)
                    .addCategory(Intent.CATEGORY_HOME)
                    .setClassName(getPackageName(), HomeActivity.class.getName())
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT
                            | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED
                            | Intent.FLAG_ACTIVITY_NO_ANIMATION));
        } catch (Throwable e) {
            AppLog.w("trap launch failed: " + e.toString());
        }
    }

    /** Traps while the switch says Free My TV, or while an installer left the "fmtv_trap=1" marker (Fire OS). */
    private boolean trapOn() {
        String mode = HomeMode.state(this).optString("mode");
        return !HomeMode.ORIGINAL.equals(mode)
                || "1".equals(android.provider.Settings.Global.getString(getContentResolver(), "fmtv_trap"));
    }

    @Override public void onInterrupt() {}

    private static long lastBeat;

    /** Touches a liveness file every ~2.5 s so the ":home" guard can tell a dead service from a live one. */
    private void heartbeat() {
        long now = System.currentTimeMillis();
        if (now - lastBeat < 2500) return;
        lastBeat = now;
        try {
            java.io.FileOutputStream out = new java.io.FileOutputStream(new java.io.File(getFilesDir(), "trap.beat"));
            out.write(new byte[] {1});
            out.close();
        } catch (java.io.IOException ignored) {}
    }

    /** Fire TV: polls the active window so a Home press with the launcher already on top is caught too. */
    private void poll() {
        heartbeat();
        if (wasDreamingOrScreenOff) {
            wasDreamingOrScreenOff = false;
            AccessibilityNodeInfo root = getRootInActiveWindow();
            CharSequence p;
            try {
                p = root == null ? null : root.getPackageName();
            } finally {
                recycle(root);
            }
            if (p != null && !"io.freemytv".contentEquals(p)) {
                dismissCurrentAppAndGoHome();
                if (handler != null) handler.postDelayed(this::poll, 80);
                return;
            }
        }
        if (fmtvForeground) {
            if (handler != null) handler.postDelayed(this::poll, 500);
            return;
        }
        AccessibilityNodeInfo root = getRootInActiveWindow();
        CharSequence p;
        try {
            p = root == null ? null : root.getPackageName();
        } finally {
            recycle(root);
        }
        boolean launcher = p != null && "com.amazon.tv.launcher".contentEquals(p);
        launcherTicks = launcher ? launcherTicks + 1 : 0;
        if (launcher && launcherTicks >= 2 && Prefs.homeTrap() && trapOn()
                && isHomeClass(lastLauncherActivity)
                && System.currentTimeMillis() - lastTrap >= 80) {
            lastTrap = System.currentTimeMillis();
            tryLaunch();
        }
        if (handler != null) handler.postDelayed(this::poll, 150);
    }

    /** Nodes are pooled by the framework before API 33: give them back (no-op on newer Androids). */
    private static void recycle(AccessibilityNodeInfo node) {
        if (node == null || android.os.Build.VERSION.SDK_INT >= 33) return;
        node.recycle();
    }

    /** True only for the launcher's HOME screen; its own settings screens (MainSettingsActivity) stay open. */
    private static boolean isHomeClass(CharSequence c) {
        if (c == null || c.length() == 0) return true;
        String s = c.toString();
        return s.contains("HomeActivity") && !s.contains("Settings");
    }

    @Override public void onServiceConnected() {
        super.onServiceConnected();
        handler = new android.os.Handler(android.os.Looper.getMainLooper());
        handler.postDelayed(this::poll, 200);

        if (screenReceiver == null) {
            screenReceiver = new BroadcastReceiver() {
                @Override public void onReceive(Context context, Intent intent) {
                    if (intent == null) return;
                    String action = intent.getAction();
                    if (Intent.ACTION_SCREEN_OFF.equals(action)
                            || "android.intent.action.DREAMING_STARTED".equals(action)) {
                        wasDreamingOrScreenOff = true;
                        dismissCurrentAppAndGoHome();
                    } else if (Intent.ACTION_SCREEN_ON.equals(action)
                            || Intent.ACTION_USER_PRESENT.equals(action)
                            || "android.intent.action.DREAMING_STOPPED".equals(action)
                            || "android.intent.action.HDMI_PLUGGED".equals(action)
                            || "android.media.action.HDMI_AUDIO_PLUG".equals(action)) {
                        wasDreamingOrScreenOff = true;
                        dismissCurrentAppAndGoHome();
                    }
                }
            };
            IntentFilter filter = new IntentFilter();
            filter.addAction(Intent.ACTION_SCREEN_OFF);
            filter.addAction(Intent.ACTION_SCREEN_ON);
            filter.addAction(Intent.ACTION_USER_PRESENT);
            filter.addAction("android.intent.action.DREAMING_STARTED");
            filter.addAction("android.intent.action.DREAMING_STOPPED");
            filter.addAction("android.intent.action.HDMI_PLUGGED");
            filter.addAction("android.media.action.HDMI_AUDIO_PLUG");
            registerReceiver(screenReceiver, filter);
        }

        try {
            android.hardware.display.DisplayManager dm = (android.hardware.display.DisplayManager) getSystemService(Context.DISPLAY_SERVICE);
            if (dm != null && displayListener == null) {
                displayListener = new android.hardware.display.DisplayManager.DisplayListener() {
                    @Override public void onDisplayAdded(int displayId) {
                        wasDreamingOrScreenOff = true;
                        dismissCurrentAppAndGoHome();
                    }
                    @Override public void onDisplayRemoved(int displayId) {
                        wasDreamingOrScreenOff = true;
                        dismissCurrentAppAndGoHome();
                    }
                    @Override public void onDisplayChanged(int displayId) {
                        wasDreamingOrScreenOff = true;
                        dismissCurrentAppAndGoHome();
                    }
                };
                dm.registerDisplayListener(displayListener, handler);
            }
        } catch (Throwable ignored) {}
    }

    @Override public boolean onUnbind(android.content.Intent intent) {
        if (handler != null) handler.removeCallbacksAndMessages(null);
        if (screenReceiver != null) {
            try { unregisterReceiver(screenReceiver); } catch (Throwable ignored) {}
            screenReceiver = null;
        }
        if (displayListener != null) {
            try {
                android.hardware.display.DisplayManager dm = (android.hardware.display.DisplayManager) getSystemService(Context.DISPLAY_SERVICE);
                if (dm != null) dm.unregisterDisplayListener(displayListener);
            } catch (Throwable ignored) {}
            displayListener = null;
        }
        return super.onUnbind(intent);
    }
}
