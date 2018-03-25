package com.monroe.movement.experimentmgr;

/**
 * Created by marios on 04/10/2017.
 */

import android.content.Intent;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.text.method.ScrollingMovementMethod;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.WindowManager;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.ToggleButton;
import android.support.v7.widget.Toolbar;

import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttMessage;

import org.eclipse.paho.client.mqttv3.MqttCallbackExtended;

// main activity
public class MainActivity extends AppCompatActivity {

    private static final int SETTINGS_ACTIVITY_RESULT_CODE = 0;

    private String nrounds="2", test_list="", save_db="no", nodeid = "171", brokerip = "192.168.1.2", username = "user", password = "pass";
    private MqttHelper mqttHelperSubD, mqttHelperSubE;
    private TextView tvD1, tvE1, tvN1;
    private EditText etE3;
    private ToggleButton toggleButtonD1, toggleButtonE1;
    private CheckBox chk1, chk2, chk3, chk4, chk5, chk6, chk7, chk8;


    public void clickButtonD1(View view){
        clickButton("startdocker", "monroe/" + nodeid + "/docker");
    }

    public void clickButtonD2(View view){
        clickButton("stopdocker", "monroe/" + nodeid + "/docker");
    }

    public void clickButtonD3(View view){
        clickButton("psdocker", "monroe/" + nodeid + "/docker");
    }

    public void clickButtonD4(View view){
        tvD1.setText("");
    }

    public void clickButtonE3(View view){
        tvE1.setText("");
    }

    public void clickButtonE1(View view){

        if (onCheckBoxClicked())
            clickButton("start:"+nrounds+":"+test_list+":"+save_db, "monroe/" + nodeid + "/experiment");
        else
            Toast.makeText(getApplicationContext(),"Please give a number for rounds", Toast.LENGTH_SHORT).show();
    }

    public void clickButtonE2(View view){
        clickButton("stop", "monroe/" + nodeid + "/experiment");
    }

    //publish mqtt message to topic in mqtt broker
    public void clickButton(String messageStr, String pubTopic){
        Log.i("Info","publish: "+messageStr);
        Toast.makeText(getApplicationContext(),"publish: "+messageStr + " in " +pubTopic,
                Toast.LENGTH_SHORT).show();
        //tv1.setText("Welcome to android");
        String serverUri = "tcp://" + brokerip + ":1883";
        String subscriptionTopic = pubTopic;
        MqttHelper mqttHelperPub;
        mqttHelperPub = new MqttHelper(getApplicationContext(), serverUri, subscriptionTopic, username, password);
        mqttHelperPub.setCallback(new MqttCallbackExtended() {
            @Override
            public void connectComplete(boolean b, String s) {
            }
            @Override
            public void connectionLost(Throwable throwable) {
            }
            @Override
            public void messageArrived(String topic, MqttMessage mqttMessage) throws Exception {
            }
            @Override
            public void deliveryComplete(IMqttDeliveryToken iMqttDeliveryToken) {
                Toast.makeText(getApplicationContext(),"message delivered",
                        Toast.LENGTH_SHORT).show();
            }
        });
        mqttHelperPub.publish(messageStr);
    }

    public void onToggleClickedD1(View view){
        onToggleClicked(view, tvD1, "monroe/" + nodeid + "/dockerFB");
    }

    public void onToggleClickedE1(View view){
        onToggleClicked(view, tvE1, "monroe/" + nodeid + "/experimentFB");
    }

    //subscribe to topic in mqtt broker
    public void onToggleClicked(View view, final TextView tv, String subTopic){
        MqttHelper mqttHelperSub;
        if(((ToggleButton) view).isChecked()) {
            //tv.setText("ON");
            String serverUri = "tcp://" + brokerip + ":1883";
            String subscriptionTopic = subTopic;
            mqttHelperSub = new MqttHelper(getApplicationContext(), serverUri, subscriptionTopic, username, password);
            mqttHelperSub.setCallback(new MqttCallbackExtended() {
                @Override
                public void connectComplete(boolean b, String s) {
                }
                @Override
                public void connectionLost(Throwable throwable) {
                }
                @Override
                public void messageArrived(String topic, MqttMessage mqttMessage) throws Exception {
                    Log.w("Debug",mqttMessage.toString());
                    //tv.setText(mqttMessage.toString());
                    tv.append(mqttMessage.toString()+"\n");

                    final int scrollAmount = tv.getLayout().getLineTop(tv.getLineCount()) - tv.getHeight();
                    // if there is no need to scroll, scrollAmount will be <=0
                    if (scrollAmount > 0)
                        tv.scrollTo(0, scrollAmount);
                    else
                        tv.scrollTo(0, 0);
                }
                @Override
                public void deliveryComplete(IMqttDeliveryToken iMqttDeliveryToken) {
                }
            });
            mqttHelperSub.subscribe();
            if(subTopic.equals("monroe/" + nodeid + "/dockerFB"))
                mqttHelperSubD = mqttHelperSub;
            else
                mqttHelperSubE = mqttHelperSub;
        } else {
            //tv.setText("OFF");
            if(subTopic.equals("monroe/" + nodeid + "/dockerFB"))
                mqttHelperSub = mqttHelperSubD;
            else
                mqttHelperSub = mqttHelperSubE;
            mqttHelperSub.unsubscribe();
        }
    }

    //create mqtt message
    public boolean onCheckBoxClicked() {
        test_list = "";
        save_db="no";
        if (chk1.isChecked()) {
            test_list = test_list + "ping,";
        }
        if (chk2.isChecked()) {
            test_list = test_list + "iperf3_dl,";
        }
        if (chk3.isChecked()) {
            test_list = test_list + "iperf3_ul,";
        }
        if (chk4.isChecked()) {
            test_list = test_list + "curl_dl,";
        }
        if (chk5.isChecked()) {
            test_list = test_list + "curl_ul,";
        }
        if (chk6.isChecked()) {
            test_list = test_list + "video,";
        }
        if (chk7.isChecked()) {
            test_list = test_list + "speedtest";
        }
        if (chk8.isChecked()) {
            save_db = "yes";
        }
        nrounds = etE3.getText().toString();
        return isNumeric(nrounds);
    }

    public static boolean isNumeric(String str)
    {
        try
        {
            double d = Double.parseDouble(str);
        }
        catch(NumberFormatException nfe)
        {
            return false;
        }
        return true;
    }


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_HIDDEN);

        Toolbar myToolbar = (Toolbar) findViewById(R.id.toolbar);
        setSupportActionBar(myToolbar);

        tvN1 = (TextView)findViewById(R.id.textViewN1);
        tvN1.setText("Node# ");
        tvD1 = (TextView)findViewById(R.id.textViewD1);
        tvD1.setMovementMethod(new ScrollingMovementMethod());
        tvE1 = (TextView)findViewById(R.id.textViewE1);
        tvE1.setMovementMethod(new ScrollingMovementMethod());
        etE3 = (EditText) findViewById(R.id.editTextE3);
        chk1 = (CheckBox) findViewById(R.id.checkBox1);
        chk2 = (CheckBox) findViewById(R.id.checkBox2);
        chk3 = (CheckBox) findViewById(R.id.checkBox3);
        chk4 = (CheckBox) findViewById(R.id.checkBox4);
        chk5 = (CheckBox) findViewById(R.id.checkBox5);
        chk6 = (CheckBox) findViewById(R.id.checkBox6);
        chk7 = (CheckBox) findViewById(R.id.checkBox7);
        chk8 = (CheckBox) findViewById(R.id.checkBox8);
    }

    // Menu icons are inflated just as they were with actionbar
    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        switch (item.getItemId()) {
            case R.id.action_settings:
                // User chose the "Settings" item, show the app settings UI...
                Intent myIntent = new Intent(this, MyChildActivity.class);
                startActivityForResult(myIntent, SETTINGS_ACTIVITY_RESULT_CODE);
                return true;
            default:
                // If we got here, the user's action was not recognized.
                // Invoke the superclass to handle it.
                return super.onOptionsItemSelected(item);
        }
    }

    // This method is called when the child activity finishes
    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        // check that it is the SecondActivity with an OK result
        if (requestCode == SETTINGS_ACTIVITY_RESULT_CODE) {
            if (resultCode == RESULT_OK) {
                brokerip = data.getStringExtra("broker_ip");
                username = data.getStringExtra("username");
                password = data.getStringExtra("password");
                nodeid = data.getStringExtra("node_id");
                tvN1.setText("Node# " + nodeid);
            }
        }
    }

}
