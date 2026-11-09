package fr.monevolution.app;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.res.AssetFileDescriptor;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import java.io.File;
import java.io.FileNotFoundException;

/** Camera output backed by the app's private cache, granted for this one capture. */
public final class CameraPhotoProvider extends ContentProvider {
    public static final String AUTHORITY="fr.monevolution.app.camera";
    public static Uri uriFor(String filename) {
        return new Uri.Builder().scheme("content").authority(AUTHORITY)
            .appendPath(filename).build();
    }
    private File target(Uri uri) throws FileNotFoundException {
        if(uri==null || !AUTHORITY.equals(uri.getAuthority()))
            throw new FileNotFoundException("Wrong authority");
        String filename=uri.getLastPathSegment();
        if(filename==null || !filename.matches("capture-[a-f0-9-]{36}\\.jpg"))
            throw new FileNotFoundException("Invalid camera file");
        File folder=new File(getContext().getCacheDir(),"meal-camera");
        if(!folder.exists()&&!folder.mkdirs())throw new FileNotFoundException("Cache unavailable");
        return new File(folder,filename);
    }
    @Override public boolean onCreate(){return true;}
    @Override public String getType(Uri uri){return "image/jpeg";}
    @Override public Cursor query(Uri uri,String[] projection,String selection,
                                 String[] selectionArgs,String sortOrder){
        try{
            File f=target(uri);
            String[] fields=projection==null
               ?new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE}:projection;
            MatrixCursor rows=new MatrixCursor(fields);
            Object[] row=new Object[fields.length];
            for(int n=0;n<fields.length;n++){
                if(OpenableColumns.DISPLAY_NAME.equals(fields[n]))row[n]=f.getName();
                else if(OpenableColumns.SIZE.equals(fields[n]))row[n]=f.length();
            }
            rows.addRow(row);return rows;
        }catch(FileNotFoundException ex){return null;}
    }
    @Override public ParcelFileDescriptor openFile(Uri uri,String mode) throws FileNotFoundException {
        File f=target(uri);
        // Callers cannot access any path outside the specifically named camera captures.
        int flags;
        if("r".equals(mode))flags=ParcelFileDescriptor.MODE_READ_ONLY;
        else if("w".equals(mode)||"wt".equals(mode))flags=ParcelFileDescriptor.MODE_WRITE_ONLY|ParcelFileDescriptor.MODE_CREATE|ParcelFileDescriptor.MODE_TRUNCATE;
        else if("rw".equals(mode))flags=ParcelFileDescriptor.MODE_READ_WRITE|ParcelFileDescriptor.MODE_CREATE;
        else throw new FileNotFoundException("Unsupported mode");
        return ParcelFileDescriptor.open(f,flags);
    }
    @Override public int delete(Uri uri,String selection,String[] args) {
        try{return target(uri).delete()?1:0;}catch(Exception e){return 0;}
    }
    @Override public Uri insert(Uri uri,ContentValues values){throw new UnsupportedOperationException();}
    @Override public int update(Uri uri,ContentValues values,String selection,String[] args) {
        throw new UnsupportedOperationException();
    }
}
