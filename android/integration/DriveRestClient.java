package fr.monevolution.app.drive;

import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.regex.Pattern;

/**
 * REST adapter for Google Drive v3.
 * Requires an access token obtained by Google Identity AuthorizationClient with drive.file.
 * All methods are BLOCKING. Call from an I/O executor, never from the Android UI thread.
 * Do not log tokens, private profiles, or raw responses.
 */
public final class DriveRestClient {
    private static final String API = "https://www.googleapis.com/drive/v3";
    private static final String UPLOAD = "https://www.googleapis.com/upload/drive/v3";
    private static final Pattern VALID_ID = Pattern.compile("[A-Za-z0-9_-]{5,256}");
    private final String token;

    public DriveRestClient(String accessToken) {
        if (accessToken == null || accessToken.isEmpty()) throw new IllegalArgumentException("Missing access token");
        token = accessToken;
    }

    private static String validId(String id) {
        if (id == null || !VALID_ID.matcher(id).matches()) throw new IllegalArgumentException("Invalid file/permission id");
        return id;
    }

    private static byte[] read(InputStream in, int maxBytes) throws IOException {
        if (in == null) return new byte[0];
        try (InputStream input = in; ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = input.read(buffer)) >= 0) {
                out.write(buffer, 0, count);
                if (out.size() > maxBytes) throw new IOException("Response exceeds size limit");
            }
            return out.toByteArray();
        }
    }

    private byte[] request(String method, String path, String contentType, byte[] body, int limit) throws IOException {
        HttpURLConnection conn = (HttpURLConnection) new URL(path).openConnection();
        conn.setConnectTimeout(15000);
        conn.setReadTimeout(30000);
        if ("PATCH".equals(method)) {
            // Android HttpURLConnection does not implement PATCH; Google Drive supports this override.
            conn.setRequestMethod("POST");
            conn.setRequestProperty("X-HTTP-Method-Override", "PATCH");
        } else {
            conn.setRequestMethod(method);
        }
        conn.setRequestProperty("Authorization", "Bearer " + token);
        conn.setRequestProperty("Accept", "application/json");
        if (body != null) {
            conn.setDoOutput(true);
            conn.setRequestProperty("Content-Type", contentType);
            conn.setFixedLengthStreamingMode(body.length);
        }
        try {
            if (body != null) {
                try (OutputStream out = conn.getOutputStream()) { out.write(body); }
            }
            int status = conn.getResponseCode();
            byte[] response = read(status >= 200 && status < 300
                    ? conn.getInputStream() : conn.getErrorStream(), limit);
            if (status < 200 || status >= 300) {
                // Never expose response body; it can contain private metadata.
                throw new IOException("Drive API request failed (HTTP " + status + ")");
            }
            return response;
        } finally {
            conn.disconnect();
        }
    }

    /** Creates a Drive JSON file, returning its stable file ID. */
    public String createJsonFile(String filename, String json) throws Exception {
        if (filename == null || filename.length() > 120 || json == null || json.length() > 20_000_000)
            throw new IllegalArgumentException("Invalid file");
        JSONObject metadata = new JSONObject();
        metadata.put("name", filename);
        metadata.put("mimeType", "application/json");
        String boundary = "monEvolutionImcBoundary";
        String header = "--" + boundary + "\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
                + metadata.toString() + "\r\n--" + boundary
                + "\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n";
        String footer = "\r\n--" + boundary + "--\r\n";
        ByteArrayOutputStream body = new ByteArrayOutputStream();
        body.write(header.getBytes(StandardCharsets.UTF_8));
        body.write(json.getBytes(StandardCharsets.UTF_8));
        body.write(footer.getBytes(StandardCharsets.UTF_8));
        byte[] result = request("POST", UPLOAD + "/files?uploadType=multipart&fields=id",
                "multipart/related; boundary=" + boundary, body.toByteArray(), 500_000);
        return validId(new JSONObject(new String(result, StandardCharsets.UTF_8)).getString("id"));
    }

    /** Updates the SAME Drive file ID, not a new duplicate. */
    public void updateJsonFile(String fileId, String json) throws Exception {
        if (json == null || json.length() > 20_000_000) throw new IllegalArgumentException("Invalid data");
        request("PATCH", UPLOAD + "/files/" + validId(fileId) + "?uploadType=media",
                "application/json; charset=UTF-8", json.getBytes(StandardCharsets.UTF_8), 500_000);
    }

    /** Reads an existing authorized JSON file. */
    public String readJsonFile(String fileId) throws Exception {
        byte[] bytes = request("GET", API + "/files/" + validId(fileId) + "?alt=media",
                null, null, 30_000_000);
        return new String(bytes, StandardCharsets.UTF_8);
    }

    /** Invites a specific Google account with reader access; never public/anyone. */
    public String inviteReader(String fileId, String email) throws Exception {
        if (email == null || email.length() > 254 || !email.matches("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"))
            throw new IllegalArgumentException("Invalid email");
        JSONObject permission = new JSONObject();
        permission.put("type", "user");
        permission.put("role", "reader");
        permission.put("emailAddress", email);
        byte[] result = request("POST", API + "/files/" + validId(fileId)
                        + "/permissions?fields=id%2Crole%2CemailAddress&sendNotificationEmail=true",
                "application/json; charset=UTF-8",
                permission.toString().getBytes(StandardCharsets.UTF_8), 500_000);
        return validId(new JSONObject(new String(result, StandardCharsets.UTF_8)).getString("id"));
    }

    public JSONObject listPermissions(String fileId) throws Exception {
        byte[] result = request("GET", API + "/files/" + validId(fileId)
                + "/permissions?fields=permissions(id%2CemailAddress%2Crole%2Ctype)%2CnextPageToken",
                null, null, 500_000);
        return new JSONObject(new String(result, StandardCharsets.UTF_8));
    }

    /** Revokes a reader by permission ID; do not attempt to delete the owner. */
    public void revokeReader(String fileId, String permissionId) throws Exception {
        request("DELETE", API + "/files/" + validId(fileId) + "/permissions/"
                + validId(permissionId), null, null, 500_000);
    }
}
