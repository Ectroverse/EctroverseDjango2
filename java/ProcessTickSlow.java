package org.ectroverse.processtick;

import java.io.*;
import java.sql.*;
import java.util.*;
import java.time.Clock; 
import java.time.Instant; 
import java.util.concurrent.*;
import java.util.Arrays.*;
import java.text.SimpleDateFormat;
import static org.ectroverse.processtick.Constants.*;


public class ProcessTickSlow
{
    public static void main(String[] args) {
		long startTime = System.nanoTime();
		long connectionTime = 0;
				
		Connection tmpCon = null;
		try{
			tmpCon = DriverManager.getConnection(Settings.connectionPath, Settings.dbUserName, Settings.dbPass);
		}
		catch (Exception e) {
			System.out.println("exception " +  e.getMessage());
			System.out.println("Connection with postgres DB not established, aborting." );
			System.exit(0);
		}
		final Connection con = tmpCon;
		
		System.out.println("connection time " + (double)(connectionTime - startTime)/1_000_000_000.0 + " sec.");
		
		ScheduledExecutorService s = Executors.newSingleThreadScheduledExecutor();
		Calendar calendar = Calendar.getInstance();
		ProcessTickSlow pt = new ProcessTickSlow();
		Runnable scheduledTask = new Runnable() {
			public void run() {
				pt.processTick(con);
			}
		};
		
		//use this for 10 second tick

		long millistoNext = HelperFunctions.startDelay(calendar, Settings.tickTime);	
		long currentTime = System.currentTimeMillis();
		long tickScheduleTime = currentTime + millistoNext;
		
		SimpleDateFormat sdf = new SimpleDateFormat("EEE, d MMM yyyy HH:mm:ss Z");   
		java.util.Date current = new java.util.Date(currentTime);		
		java.util.Date resultdate = new java.util.Date(tickScheduleTime);

		System.out.println("Current time: " + sdf.format(current));
		System.out.println("Tick start scheduled at " + sdf.format(resultdate));
		s.scheduleAtFixedRate(scheduledTask, millistoNext, Settings.tickTime*1000, TimeUnit.MILLISECONDS);
		
		
		//use this for 10 minute tick
		// long millistoNext = HelperFunctions.secondsToFirstOccurence600(calendar);	
		// s.scheduleAtFixedRate(scheduledTask, millistoNext, 600*1000, TimeUnit.MILLISECONDS);
	}

	private void processTick(Connection con){
		
		long beginTime = System.nanoTime();
		
		Statement statement;
		
		ResultSet opcount = null;
		ResultSet inccount = null;
		try {
			statement = con.createStatement();
			statement.executeUpdate("call calc_tick('slow');"); 
		}
		catch (SQLException ex){
			ex.printStackTrace();
		}
		
		long ops_time = System.nanoTime();
		System.out.println("Execute postgres regular tick: " + (double)(ops_time-beginTime)/1_000_000_000.0 + " sec.");
		try {

			statement = con.createStatement();
			opcount = statement.executeQuery("SELECT count(*) as count FROM app_fleet where command_order = 6 and ticks_remaining = 0");
			opcount.next();
			int opc = opcount.getInt("count");
			if (opc > 0 ){
				statement.executeUpdate("call operations(1);");
				long ops_end = System.nanoTime();
				System.out.println("Operations time: " + (double)(ops_end-ops_time)/1_000_000_000.0 + " sec.");
			}
		
			long inca_time = System.nanoTime();
			inccount = statement.executeQuery("SELECT count(*) as count FROM app_fleet where command_order = 7 and ticks_remaining = 0");
			inccount.next();
			int inca = inccount.getInt("count");
			if (inca > 0 ){
				statement.executeUpdate("call incantations(1);");
				long inca_end = System.nanoTime();
				System.out.println("Incantations time: " + (double)(inca_end-inca_time)/1_000_000_000.0 + " sec.");
			}
			 
		}
		catch (SQLException ex){
			ex.printStackTrace();
		}

		long endTime = System.nanoTime();
		
		System.out.println("Total time: " + (double)(endTime-beginTime)/1_000_000_000.0 + " sec.");
		
	}
}
