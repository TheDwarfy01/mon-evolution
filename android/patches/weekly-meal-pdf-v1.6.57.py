#!/usr/bin/env python3
"""Add a two-page A4 landscape weekly meals PDF with a Monday-Sunday selector."""
from pathlib import Path
root=Path("android/source-1.6.57/app")
java=root/"src/main/java/fr/monevolution/app/MainActivity.java"
html=root/"src/main/assets/index.html"
def replace_one(path,old,new):
    source=path.read_text(encoding="utf-8")
    count=source.count(old)
    if count != 1: raise AssertionError(f"{path}: {count} matches for {old[:100]!r}")
    path.write_text(source.replace(old,new),encoding="utf-8")
replace_one(java,"PROGRESS_PDF = 51, PHOTO_CAMERA = 52;", "PROGRESS_PDF = 51, PHOTO_CAMERA = 52, WEEKLY_MEALS_PDF = 53;")
replace_one(java,"private String pendingPdfJson;", "private String pendingPdfJson;\n    private String pendingWeeklyPdfJson;")
replace_one(java,'if(!("progress".equals(kind)||"meals".equals(kind))',
                 'if(!("progress".equals(kind)||"meals".equals(kind)||"weekly".equals(kind))')
replace_one(java,'''                    }else{
                        if(!doc.getString("month").matches("\\\\d{4}-\\\\d{2}"))
                            throw new Exception("Mois invalide");
                        if(doc.getJSONArray("days").length()>366)
                            throw new Exception("Trop de jours");
                    }
                    temporary=File.createTempFile''',
'''                    }else if("weekly".equals(kind)){
                        if(!doc.getString("start").matches("\\\\d{4}-\\\\d{2}-\\\\d{2}"))
                            throw new Exception("Semaine invalide");
                        if(doc.getJSONObject("days").length()>7)
                            throw new Exception("Trop de jours");
                    }else{
                        if(!doc.getString("month").matches("\\\\d{4}-\\\\d{2}"))
                            throw new Exception("Mois invalide");
                        if(doc.getJSONArray("days").length()>366)
                            throw new Exception("Trop de jours");
                    }
                    temporary=File.createTempFile''')
replace_one(java,'''                        if("progress".equals(kind))createProgressPdf(output,reportJson);
                        else createMealsPdf(output,reportJson);''',
'''                        if("progress".equals(kind))createProgressPdf(output,reportJson);
                        else if("weekly".equals(kind))createWeeklyMealsPdf(output,reportJson);
                        else createMealsPdf(output,reportJson);''')
replace_one(java,'''        @JavascriptInterface public void exportMealsPdf(String reportJson) {''',
'''        @JavascriptInterface public void exportWeeklyMealsPdf(String reportJson) {
            if(reportJson==null||reportJson.length()>6_000_000){js("exportFailed()");return;}
            runOnUiThread(()->{
                try{
                    JSONObject report=new JSONObject(reportJson);
                    String start=report.getString("start");
                    if(!start.matches("\\\\d{4}-\\\\d{2}-\\\\d{2}")||report.getJSONObject("days").length()>7)
                        throw new Exception("Invalid weekly report");
                    pendingWeeklyPdfJson=reportJson;
                    Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT);
                    intent.addCategory(Intent.CATEGORY_OPENABLE);
                    intent.setType("application/pdf");
                    intent.putExtra(Intent.EXTRA_TITLE,"repas-semaine-"+start+".pdf");
                    startActivityForResult(intent,WEEKLY_MEALS_PDF);
                }catch(Exception e){js("exportFailed()");}
            });
        }
        @JavascriptInterface public void exportMealsPdf(String reportJson) {''')
replace_one(java,'''            } else if (request == PROGRESS_PDF) {''',
'''            } else if (request == WEEKLY_MEALS_PDF) {
                String report=pendingWeeklyPdfJson;
                io.execute(()->{
                    try(OutputStream out=getContentResolver().openOutputStream(uri,"wt")){
                        if(out==null)throw new Exception("Destination unavailable");
                        createWeeklyMealsPdf(out,report);
                        js("pdfCompleted()");
                    }catch(Exception e){js("exportFailed()");}
                });
            } else if (request == PROGRESS_PDF) {''')
pdf=Path("android/patches/weekly-meal-pdf-v1.6.56.java.txt").read_text(encoding="utf-8")
replace_one(java,"    private void createMealsPdf(Uri uri, String reportJson) throws Exception {",pdf+"\n    private void createMealsPdf(Uri uri, String reportJson) throws Exception {")
ui=Path("android/patches/weekly-meal-pdf-v1.6.56.html.txt").read_text(encoding="utf-8")
replace_one(html,"</body></html>",ui+"\n</body></html>")
print("Weekly A4 landscape export and preview (7 days, 6 meal rows, 2 pages) integrated.")
