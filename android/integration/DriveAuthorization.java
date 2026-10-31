package fr.monevolution.app.drive;

import android.app.Activity;
import android.app.PendingIntent;
import android.content.Intent;
import android.content.IntentSender;

import com.google.android.gms.auth.api.identity.AuthorizationClient;
import com.google.android.gms.auth.api.identity.AuthorizationRequest;
import com.google.android.gms.auth.api.identity.AuthorizationResult;
import com.google.android.gms.auth.api.identity.Identity;
import com.google.android.gms.common.api.Scope;

import java.util.Collections;

/**
 * Google Identity AuthorizationClient wrapper, for Drive file access only.
 * Add com.google.android.gms:play-services-auth:22.0.0 to build.gradle.
 *
 * Use from the native Activity, NEVER from JavaScript injected into WebView.
 * Do not store or log access tokens. Re-authorize before network operations
 * as a token may expire. Do not add a client secret to this Android application.
 */
public final class DriveAuthorization {
    public interface Callback {
        /** Called with a temporary OAuth token. Keep it in the native layer only. */
        void onAuthorized(String accessToken);
        void onError(String message);
    }

    public static final int REQUEST_CODE = 1515;
    public static final String DRIVE_FILE_SCOPE = "https://www.googleapis.com/auth/drive.file";

    private final Activity activity;
    private final AuthorizationClient client;
    private Callback pending;

    public DriveAuthorization(Activity activity) {
        this.activity = activity;
        this.client = Identity.getAuthorizationClient(activity);
    }

    /** Request authorization only after a user chooses a Drive feature. */
    public void authorize(Callback callback) {
        pending = callback;
        AuthorizationRequest request = AuthorizationRequest.builder()
                .setRequestedScopes(Collections.singletonList(new Scope(DRIVE_FILE_SCOPE)))
                .build();

        client.authorize(request)
                .addOnSuccessListener(result -> {
                    if (result.hasResolution()) {
                        PendingIntent intent = result.getPendingIntent();
                        try {
                            activity.startIntentSenderForResult(intent.getIntentSender(), REQUEST_CODE,
                                    null, 0, 0, 0);
                        } catch (IntentSender.SendIntentException ex) {
                            fail("La fenêtre d'autorisation Google ne peut pas s'ouvrir.");
                        }
                    } else {
                        accept(result);
                    }
                })
                .addOnFailureListener(error -> fail("Connexion Google indisponible."));
    }

    /** Delegate the Activity's onActivityResult here. Returns true if handled. */
    public boolean onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode != REQUEST_CODE) return false;
        if (resultCode != Activity.RESULT_OK || data == null) {
            fail("Autorisation Google annulée.");
            return true;
        }
        try {
            accept(client.getAuthorizationResultFromIntent(data));
        } catch (Exception error) {
            fail("L'autorisation Google a échoué.");
        }
        return true;
    }

    private void accept(AuthorizationResult result) {
        String accessToken = result.getAccessToken();
        if (accessToken == null || accessToken.isEmpty()) {
            fail("Jeton Google non disponible.");
            return;
        }
        Callback callback = pending;
        pending = null;
        if (callback != null) callback.onAuthorized(accessToken);
    }

    private void fail(String message) {
        Callback callback = pending;
        pending = null;
        if (callback != null) callback.onError(message);
    }
}
