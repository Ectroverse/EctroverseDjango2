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


public class ProcessTick_New
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
		ProcessTick_New pt = new ProcessTick_New();
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
		try {

			statement = con.createStatement();
			statement.executeUpdate("call calc_tick('fast');");
			
			// for slow tick
			//statement.executeUpdate("call calc_tick('slow');"); 
		}
		catch (SQLException ex){
			ex.printStackTrace();
		}
		
		long python_script1 = System.nanoTime();
		try{
			// for slow tick
			//ProcessBuilder pb = new ProcessBuilder("python", "/code/manage.py", "process_ops");
			
			ProcessBuilder pb = new ProcessBuilder("python", "/code/manage.py", "process_py");
			Process p = pb.start();

		}
		catch (Exception e){
			System.out.println("Exception: " +  e.getMessage());
		}

		long endTime = System.nanoTime();
		
		System.out.println("Execute postgres population update procedure: " + (double)(python_script1-beginTime)/1_000_000_000.0 + " sec.");
		System.out.println("Python script process_ops time: " + (double)(endTime-python_script1)/1_000_000_000.0 + " sec.");
		
	}
}
