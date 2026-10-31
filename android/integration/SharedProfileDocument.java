package fr.monevolution.app.drive;

import org.json.JSONArray;
import org.json.JSONObject;
import java.time.Instant;
import java.util.Iterator;

/**
 * Build the minimum JSON that may be shared with an invited reader.
 * Never share the full private multi-profile backup or avatar.
 */
public final class SharedProfileDocument {
    private SharedProfileDocument() {}

    private static final String[] MEAL_KEYS = {
            "morning", "morningSnack", "lunch",
            "afternoonSnack", "dinner", "eveningSnack"
    };

    public static JSONObject create(JSONObject profile, boolean includeMealPhotos) throws Exception {
        JSONObject safe = new JSONObject();
        safe.put("name", profile.getString("name"));
        safe.put("height", profile.getDouble("height"));
        safe.put("goal", profile.getDouble("goal"));

        JSONArray entries = profile.getJSONArray("entries");
        if (entries.length() < 1 || entries.length() > 20000)
            throw new IllegalArgumentException("Invalid weight history");
        JSONArray safeEntries = new JSONArray();
        for (int i = 0; i < entries.length(); i++) {
            JSONObject entry = entries.getJSONObject(i);
            JSONObject clean = new JSONObject();
            clean.put("date", entry.getString("date"));
            clean.put("weight", entry.getDouble("weight"));
            if (entry.has("note")) clean.put("note", entry.optString("note", "").substring(
                    0, Math.min(120, entry.optString("note", "").length())));
            safeEntries.put(clean);
        }
        safe.put("entries", safeEntries);

        JSONObject srcMeals = profile.optJSONObject("meals");
        JSONObject safeMeals = new JSONObject();
        if (srcMeals != null) {
            Iterator<String> dates = srcMeals.keys();
            int days = 0;
            while (dates.hasNext()) {
                String date = dates.next();
                if (!date.matches("\\d{4}-\\d{2}-\\d{2}")) continue;
                if (++days > 4000) throw new IllegalArgumentException("Too many meal days");
                JSONObject src = srcMeals.optJSONObject(date);
                if (src == null) continue;
                JSONObject safeDay = new JSONObject();
                for (String key : MEAL_KEYS) {
                    if (src.has(key)) {
                        String text = src.optString(key, "");
                        safeDay.put(key, text.substring(0, Math.min(3000, text.length())));
                    }
                    if (includeMealPhotos) {
                        String photo = src.optString(key + "Photo", "");
                        if (photo.startsWith("data:image/jpeg;base64,") && photo.length() < 250000) {
                            safeDay.put(key + "Photo", photo);
                        }
                    }
                }
                safeMeals.put(date, safeDay);
            }
        }
        safe.put("meals", safeMeals);

        JSONObject result = new JSONObject();
        result.put("format", "mon-evolution-lecture-seule");
        result.put("version", 1);
        result.put("exportedAt", Instant.now().toString());
        result.put("profile", safe);
        return result;
    }
}
