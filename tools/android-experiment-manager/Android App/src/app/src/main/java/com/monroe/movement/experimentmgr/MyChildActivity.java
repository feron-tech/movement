package com.monroe.movement.experimentmgr;

/**
 * Created by marios on 04/10/2017.
 */

import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.support.v7.app.ActionBar;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.Spinner;
import android.support.v7.widget.Toolbar;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

import android.app.Activity;
import android.content.Context;
import android.widget.Toast;


// settings activity
public class MyChildActivity extends AppCompatActivity {

    EditText chedt1, chedt2, chedt3;
    Spinner chspinner;

    public static final String MyPREFERENCES = "MyPrefs" ;
    public static final String Broker = "broker_ip";
    public static final String Username = "username";
    public static final String Password = "password";
    public static final String Node = "node_id";
    public static final String NodeList = "node_list";
    SharedPreferences sharedpreferences;

    ArrayList<String> NodeL = new ArrayList<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);

        // my_child_toolbar is defined in the layout file
        Toolbar myChildToolbar =
                (Toolbar) findViewById(R.id.child_toolbar);
        setSupportActionBar(myChildToolbar);

        // Get a support ActionBar corresponding to this toolbar
        ActionBar ab = getSupportActionBar();
        // Enable the Up button
        ab.setDisplayHomeAsUpEnabled(true);


        chedt1 = (EditText) findViewById(R.id.child_editText1);
        chedt2 = (EditText) findViewById(R.id.child_editText2);
        chedt3 = (EditText) findViewById(R.id.child_editText3);
        chspinner = (Spinner) findViewById(R.id.child_spinner1);

        Set<String> defaultSet = new HashSet<String>(Arrays.asList(getResources().getStringArray(R.array.chspinner)));

        sharedpreferences = getSharedPreferences(MyPREFERENCES, Context.MODE_PRIVATE);
        Set<String> set = sharedpreferences.getStringSet("node_list", defaultSet);
        NodeL = new ArrayList<String>(set);
        Collections.sort(NodeL, String.CASE_INSENSITIVE_ORDER);


        // Create an ArrayAdapter using the string array and a default spinner layout
        //ArrayAdapter<CharSequence> adapter = ArrayAdapter.createFromResource(this,
        //        R.array.chspinner, android.R.layout.simple_spinner_item);
        ArrayAdapter<String> adapter = new ArrayAdapter<String>(this, android.R.layout.simple_spinner_item, NodeL);
        // Specify the layout to use when the list of choices appears
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        // Apply the adapter to the spinner
        chspinner.setAdapter(adapter);

        chedt1.setText(sharedpreferences.getString(Broker, ""));
        chedt2.setText(sharedpreferences.getString(Username, ""));
        chedt3.setText(sharedpreferences.getString(Password, ""));
        chspinner.setSelection(((ArrayAdapter)chspinner.getAdapter()).getPosition(sharedpreferences.getString(Node, "")));

    }


    public void onButtonClick(View view) {

        switch (view.getId()) {
            case R.id.child_button_add:
                showAddDialog();
                break;
            case R.id.child_button_remove:
                showRemoveDialog();
                break;
            case R.id.child_button:
                // get the text from the EditText
                String stringToPassBack1 = chedt1.getText().toString();
                String stringToPassBack2 = chedt2.getText().toString();
                String stringToPassBack3 = chedt3.getText().toString();
                String stringToPassBack4 = chspinner.getSelectedItem().toString();
                Set<String> set = new HashSet<String>();
                set.addAll(NodeL);

                // use sharedpreferences to permanent store setting
                SharedPreferences.Editor editor = sharedpreferences.edit();
                editor.putString(Broker, stringToPassBack1);
                editor.putString(Username, stringToPassBack2);
                editor.putString(Password, stringToPassBack3);
                editor.putString(Node, stringToPassBack4);
                editor.putStringSet(NodeList, set);
                editor.commit();

                // put the String to pass back into an Intent and close this activity (this procedure is not needed if sharedpreferences are used)
                Intent intent = new Intent();
                intent.putExtra(Broker, stringToPassBack1);
                intent.putExtra(Username, stringToPassBack2);
                intent.putExtra(Password, stringToPassBack3);
                intent.putExtra(Node, stringToPassBack4);
                setResult(Activity.RESULT_OK, intent);
                finish();
                break;


        }
    }

    protected void showAddDialog() {

        // get prompts.xml view
        LayoutInflater layoutInflater = LayoutInflater.from(this);
        View promptView = layoutInflater.inflate(R.layout.add_dialog, null);
        AlertDialog.Builder alertDialogBuilder = new AlertDialog.Builder(this);
        alertDialogBuilder.setView(promptView);

        final EditText addText = (EditText) promptView.findViewById(R.id.adddialogtext);
        // setup a dialog window
        alertDialogBuilder.setCancelable(false)
                .setPositiveButton("OK", new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface dialog, int id) {
                        NodeL.add(addText.getText().toString());
                        Collections.sort(NodeL, String.CASE_INSENSITIVE_ORDER);
                    }
                })
                .setNegativeButton("Cancel",
                        new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface dialog, int id) {
                                dialog.cancel();
                            }
                        });

        // create an alert dialog
        AlertDialog alert = alertDialogBuilder.create();
        alert.show();
    }

    protected void showRemoveDialog() {

        // get prompts.xml view
        LayoutInflater layoutInflater = LayoutInflater.from(this);
        View promptView = layoutInflater.inflate(R.layout.remove_dialog, null);
        AlertDialog.Builder alertDialogBuilder = new AlertDialog.Builder(this);
        alertDialogBuilder.setView(promptView);

        final EditText removeText = (EditText) promptView.findViewById(R.id.removedialogtext);
        // setup a dialog window
        alertDialogBuilder.setCancelable(false)
                .setPositiveButton("OK", new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface dialog, int id) {
                        if (NodeL.remove(removeText.getText().toString())) {
                            Toast.makeText(getApplicationContext(), "Node removed", Toast.LENGTH_SHORT).show();
                        }
                        else{
                            Toast.makeText(getApplicationContext(), "Node not in list", Toast.LENGTH_SHORT).show();
                        }
                    }
                })
                .setNegativeButton("Cancel",
                        new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface dialog, int id) {
                                dialog.cancel();
                            }
                        });

        // create an alert dialog
        AlertDialog alert = alertDialogBuilder.create();
        alert.show();
    }

}
