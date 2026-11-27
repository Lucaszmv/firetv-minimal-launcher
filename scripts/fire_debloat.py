"""Lista DEBLOAT do Fire OS (pm disable-user, reversivel; ausentes sao pulados)."""
BASIC = ["com.amazon.tcomm", "com.amazon.spongy", "com.amazon.precognition", "com.amazon.ags",
         "com.amazon.bueller.photos", "com.amazon.ftv.newsqa", "com.amazon.shoptv",
         "com.amazon.shoptv.client", "com.amazon.shoptv.firetv.client", "com.amazon.hybridadidservice",
         "com.amazon.storm.lightning.tutorial", "com.amazon.gamehub", "com.amazon.smarthomemapviewapp",
         "com.amazon.tv.acr", "com.amazon.perfcollection", "com.amazon.wirelessmetrics.service"]
TELEMETRY = ["com.amazon.adep", "com.amazon.device.logmanager", "com.amazon.device.telemetry.emitter",
             "com.amazon.device.crashmanager", "com.amazon.dp.logger", "com.amazon.ftvads.deeplinking",
             "com.amazon.securitysyncclient", "com.amazon.device.sync", "com.amazon.device.sync.sdk.internal",
             "com.amazon.privacypassservice"]
FLUFF = ["com.amazon.tahoe", "com.amazon.bueller.music", "com.amazon.ftv.screensaver", "com.amazon.tv.ftvambient",
         "com.amazon.ftv.xpicker", "com.amazon.tv.ooberesource", "com.amazon.tv.releasenotes",
         "com.amazon.tv.legal.notices", "com.amazon.sneakpeek", "com.amazon.minitv.android.app",
         "com.amazon.tv.website_launcher", "com.amazon.tv.resolutioncycler",
         "com.amazon.tv.developer.dataservice", "com.amazon.tv.earlyaccess", "com.amazon.tv.consents",
         "com.amazon.sharingservice.android.client.proxy", "com.amazon.tmm.tutorial",
         "com.amazon.client.metrics.api"]
AUX = ["com.amazon.dummy.alarmclock", "com.amazon.dummy.calendar", "com.amazon.dummy.contacts",
       "com.amazon.dummy.gallery", "com.amazon.dummy.music", "com.amazon.dummy.settings",
       "com.amazon.dummy.soundpicker", "com.amazon.aiondec", "com.amazon.tv.alexaalerts",
       "com.amazon.tv.alexanotifications", "com.amazon.alexa.externalmediaplayer.fireos", "com.amazon.alexamediaplayer.runtime.ftv"]
OTA = ["com.amazon.device.software.ota", "com.amazon.device.software.ota.override", "com.amazon.tv.forcedotaupdater.v2"]  # nucleo protegido: usar ota_disable_automatic_update=1
DEBLOAT = BASIC + TELEMETRY + FLUFF + AUX + OTA
