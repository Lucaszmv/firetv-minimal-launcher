package io.freemytv;

import android.app.job.JobInfo;
import android.app.job.JobParameters;
import android.app.job.JobScheduler;
import android.app.job.JobService;
import android.content.ComponentName;
import android.content.Context;
import android.os.PersistableBundle;

/**
 * Runs the mode switches in the background (HomeMode). As a job, the system keeps the app's main process running until
 * the switch finishes, even with the screen showing something else.
 */
public class ModeJob extends JobService {
    static final String APPLY = "apply", VERIFY = "verify", REVERT = "revert", MEMORY = "memory", REMOTE = "remote",
            GUARD = "guard";
    /** Backstop for the Home Trap: its 5 s guard runs in the ":home" process and dies with it. */
    static final int GUARD_JOB_ID = 2001;
    static final long GUARD_PERIOD_MS = 15 * 60_000L;

    @Override public boolean onStartJob(JobParameters params) {
        PersistableBundle extras = params.getExtras();
        final String action = extras.getString("action", "");
        final String mode = extras.getString("mode", "");
        final Context app = getApplicationContext();
        new Thread(() -> {
            try {
                switch (action) {
                    case APPLY: HomeMode.applyNow(app, mode); break;
                    case VERIFY: HomeMode.verifyNow(app, mode); break;
                    case REVERT: HomeMode.revertHomeNow(app); break;
                    case MEMORY: HomeMode.measureMemoryNow(app, mode); break;
                    case REMOTE: HomeMode.ensureRemoteServiceNow(app); break;
                    case GUARD: HomeMode.guardTrap(app); break;
                    default: break;
                }
            } catch (Throwable t) {
                AppLog.w("job " + action + " failed: " + t);
            }
            jobFinished(params, false);
        }, "free-my-tv-" + action).start();
        return true;
    }

    @Override public boolean onStopJob(JobParameters params) {
        return false;
    }

    /** Schedules a job (one pending per action: a new request replaces the old one). */
    static void schedule(Context c, String action, String mode, long delayMs) {
        JobScheduler scheduler = c.getSystemService(JobScheduler.class);
        if (scheduler == null) return;
        PersistableBundle extras = new PersistableBundle();
        extras.putString("action", action);
        extras.putString("mode", mode == null ? "" : mode);
        JobInfo.Builder job = new JobInfo.Builder(1000 + Math.abs(action.hashCode() % 1000),
                new ComponentName(c, ModeJob.class)).setExtras(extras);
        if (delayMs > 0) job.setMinimumLatency(delayMs);
        job.setOverrideDeadline(delayMs + 2_000);
        scheduler.schedule(job.build());
    }

    /**
     * Periodic backstop for the Home Trap: the 5 s guard lives in the ":home" process, so it stops healing if that
     * process dies. One periodic job in the main process covers it; persisted so a reboot keeps it.
     */
    static void scheduleGuard(Context c) {
        try {
            JobScheduler scheduler = c.getSystemService(JobScheduler.class);
            if (scheduler == null || scheduler.getPendingJob(GUARD_JOB_ID) != null) return;
            PersistableBundle extras = new PersistableBundle();
            extras.putString("action", GUARD);
            JobInfo job = new JobInfo.Builder(GUARD_JOB_ID, new ComponentName(c, ModeJob.class))
                    .setExtras(extras).setPeriodic(GUARD_PERIOD_MS, 60_000L).setPersisted(true).build();
            scheduler.schedule(job);
        } catch (RuntimeException e) {
            AppLog.w("trap guard job not scheduled: " + e);
        }
    }
}
