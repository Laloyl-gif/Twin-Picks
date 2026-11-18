package fr.twinpicks.app;

import android.app.Activity;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.wifi.WifiManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

/**
 * Twin Picks sur Android. Au lancement (demarrage.py) :
 *  1. télécharge la dernière version du jeu depuis le dépôt GitHub (si elle a changé) ;
 *  2. cherche une partie sur le Wi-Fi : celle de l'ordinateur, ou celle d'un autre téléphone → on la rejoint ;
 *  3. sinon ouvre une partie sur ce téléphone, qui en devient l'administrateur.
 * Puis affiche le jeu (pseudo, couleur, photo… puis le menu) dans une page web plein écran.
 */
public class MainActivity extends Activity {
    private static final int FOND = Color.parseColor("#0e0c11");
    private final Handler ui = new Handler(Looper.getMainLooper());
    private WebView web;
    private LinearLayout accueil;
    private TextView message;
    private ProgressBar roue;
    private Button reessayer;
    private WifiManager.MulticastLock verrou;
    private volatile PyObject module;
    private volatile boolean pret = false;

    @Override
    protected void onCreate(Bundle etat) {
        super.onCreate(etat);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        getWindow().setStatusBarColor(FOND);
        getWindow().setNavigationBarColor(FOND);

        FrameLayout racine = new FrameLayout(this);
        racine.setBackgroundColor(FOND);

        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setCacheMode(WebSettings.LOAD_NO_CACHE);
        web.setBackgroundColor(FOND);
        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView v, WebResourceRequest r, WebResourceError e) {
                if (r.isForMainFrame()) erreur("La partie ne répond plus (Wi-Fi ?).");
            }
        });
        web.setVisibility(View.INVISIBLE);
        racine.addView(web, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        accueil = new LinearLayout(this);
        accueil.setOrientation(LinearLayout.VERTICAL);
        accueil.setGravity(Gravity.CENTER);
        accueil.setPadding(60, 60, 60, 60);
        ImageView icone = new ImageView(this);
        icone.setImageResource(R.drawable.icone);
        accueil.addView(icone, new LinearLayout.LayoutParams(260, 260));
        TextView titre = new TextView(this);
        titre.setText("Twin Picks");
        titre.setTextColor(Color.parseColor("#e9dcc0"));
        titre.setTextSize(30);
        titre.setTypeface(Typeface.SERIF);
        titre.setGravity(Gravity.CENTER);
        titre.setPadding(0, 30, 0, 30);
        accueil.addView(titre);
        roue = new ProgressBar(this);
        accueil.addView(roue);
        message = new TextView(this);
        message.setTextColor(Color.parseColor("#9a907e"));
        message.setTextSize(15);
        message.setGravity(Gravity.CENTER);
        message.setPadding(0, 30, 0, 30);
        message.setText("Démarrage…");
        accueil.addView(message);
        reessayer = new Button(this);
        reessayer.setText("Réessayer");
        reessayer.setVisibility(View.GONE);
        reessayer.setOnClickListener(v -> lancer());
        accueil.addView(reessayer);
        racine.addView(accueil, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(racine);

        WifiManager wifi = (WifiManager) getApplicationContext().getSystemService(Context.WIFI_SERVICE);
        if (wifi != null) {                       // pour entendre les réponses des parties du Wi-Fi
            verrou = wifi.createMulticastLock("twinpicks");
            verrou.setReferenceCounted(false);
            verrou.acquire();
        }
        lancer();
    }

    private void lancer() {
        pret = false;
        accueil.setVisibility(View.VISIBLE);
        roue.setVisibility(View.VISIBLE);
        reessayer.setVisibility(View.GONE);
        web.setVisibility(View.INVISIBLE);
        new Thread(() -> {
            try {
                if (!Python.isStarted()) Python.start(new AndroidPlatform(this));
                module = Python.getInstance().getModule("demarrage");
                ui.post(suivi);
                String url = module.callAttr("demarrer", getFilesDir().getAbsolutePath(), BuildConfig.DEPOT,
                        getApplicationInfo().nativeLibraryDir).toString();
                ui.post(() -> {
                    pret = true;
                    web.loadUrl(url);
                    web.setVisibility(View.VISIBLE);
                    accueil.setVisibility(View.GONE);
                });
            } catch (Throwable t) {
                String m = t.getMessage() == null ? t.toString() : t.getMessage();
                int i = m.lastIndexOf("Error: ");
                erreur(i >= 0 ? m.substring(i + 7) : m);
            }
        }).start();
    }

    private final Runnable suivi = new Runnable() {
        @Override
        public void run() {
            if (pret || module == null) return;
            try {
                message.setText(module.callAttr("message").toString());
            } catch (Throwable ignore) {
            }
            ui.postDelayed(this, 300);
        }
    };

    private void erreur(String texte) {
        ui.post(() -> {
            pret = true;
            web.setVisibility(View.INVISIBLE);
            accueil.setVisibility(View.VISIBLE);
            roue.setVisibility(View.GONE);
            message.setText(texte);
            reessayer.setVisibility(View.VISIBLE);
        });
    }

    @Override
    public void onBackPressed() {
        if (web.getVisibility() == View.VISIBLE && web.canGoBack()) web.goBack();
        else moveTaskToBack(true);              // la partie continue (ce téléphone l'héberge peut-être)
    }

    @Override
    protected void onDestroy() {
        if (verrou != null && verrou.isHeld()) verrou.release();
        super.onDestroy();
    }
}
