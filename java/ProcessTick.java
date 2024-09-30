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


public class ProcessTick
{
    public static void main(String[] args) {
		long startTime = System.nanoTime();
		long connectionTime = 0;
		
		Connection tmpCon = null;
		try{
			tmpCon = DriverManager.getConnection(Settings.connectionPath, Settings.dbUserName, Settings.dbPass);
			
			//create stored procedure - update population on planets, one of the biggest updates
			String createSP = "CREATE OR REPLACE PROCEDURE updatePlanets( "
				+ " pop_rc DOUBLE PRECISION, race_pop_growth DOUBLE PRECISION, user_id IN \"PLANET\".ID%TYPE)"
				+ "LANGUAGE SQL"
				+ " AS $$"
				+ " UPDATE \"PLANET\" SET max_population = (" + 
				+ building_production_cities + " * cities +  size * " + population_size_factor + ") *pop_rc WHERE owner_id = user_id;" 
				+ " UPDATE \"PLANET\" SET current_population = "
				+ "greatest(least(current_population + current_population * pop_rc * race_pop_growth, max_population),3000) WHERE owner_id = user_id;" 
				+ " $$;";
			
			Statement statementSP = tmpCon.createStatement();
			statementSP.execute(createSP);
			connectionTime = System.nanoTime();
		}
		catch (Exception e) {
			try{
				tmpCon.rollback();
			}
			catch (Exception ex) {
				System.out.println("exception " +  ex.getMessage());
			}
			System.out.println("exception " +  e.getMessage());
			System.out.println("Connection with postgres DB not established, aborting." );
			System.exit(0);
		}
		final Connection con = tmpCon;
		
		System.out.println("connection time " + (double)(connectionTime - startTime)/1_000_000_000.0 + " sec.");
		
		ScheduledExecutorService s = Executors.newSingleThreadScheduledExecutor();
		Calendar calendar = Calendar.getInstance();
		ProcessTick pt = new ProcessTick();
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
    
	private final String userStatusUpdateQuery = "UPDATE app_userstatus SET "+
	" fleet_readiness  = ? ," +  //1
	" psychic_readiness  = ? ," + //2
	" agent_readiness  = ? ," + //3
	" population   = ? ," + //4
	" total_solar_collectors  = ? ," + //5
	" total_fission_reactors  = ? ," + //6
	" total_mineral_plants  = ? ," + //7
	" total_crystal_labs  = ? ," + //8
	" total_refinement_stations   = ? ," + //9
	" total_cities  = ? ," + //10
	" total_research_centers   = ? ," + //11
	" total_defense_sats    = ? ," + //12
	" total_shield_networks   = ? ," + //13
	" total_portals  = ? ," + //14
	" research_points_military   = ? ," + //15
	" research_points_construction   = ? ," + //16
	" research_points_tech   = ? ," + //17
	" research_points_energy    = ? ," + //18
	" research_points_population   = ? ," + //19
	" research_points_culture    = ? ," + //20
	" research_points_operations   = ? ," + //21
	" research_points_portals    = ? ," + //22
	" current_research_funding    = ? ," + //23
	" research_percent_military   = ? ," + //24
	" research_percent_construction    = ? ," + //25
	" research_percent_tech            = ? ," + //26
	" research_percent_energy          = ? ," + //27
	" research_percent_population      = ? ," + //28
	" research_percent_culture         = ? ," + //29
	" research_percent_operations      = ? ," + //30
	" research_percent_portals         = ? ," + //31
	" energy_production          = ? ," + //32
	" energy_decay          = ? ," + //33
	" buildings_upkeep          = ? ," + //34
	" units_upkeep          = ? ," + //35
	" population_upkeep_reduction           = ? ," + //36
	" portals_upkeep           = ? ," + //37
	" mineral_production           = ? ," + //38
	" crystal_production            = ? ," + //39
	" crystal_decay            = ? ," + //40
	" ectrolium_production             = ? ," + //41
	" energy_interest              = ? ," + //42
	" mineral_interest              = ? ," + //43
	" crystal_interest              = ? ," + //44
	" ectrolium_interest              = ? ," + //45
	" energy_income              = ? ," + //46
	" mineral_income              = ? ," + //47
	" crystal_income              = ? ," + //48
	" ectrolium_income              = ? ," + //49
	" energy                  = ? ," + //50
	" minerals                = ? ," + //51
	" crystals                = ? ," + //52
	" ectrolium               = ? ," + //53
	" networth                = ? ," + //54
	" num_planets = ? ," + //55
	" construction_flag = ? ," +//56
	" economy_flag = ? ," + //57
	" military_flag = ? ," +//58
	" total_buildings  = ? , " + //59
	" energy_specop_effect  = ? , " + //60
	" mineral_decay = ? , " + //61
	" ectrolium_decay = ? " + //62
	" WHERE id = ?" ; //63 wow what a long string :P
	
	private void processTick(Connection con){
		long startTime = 0, resultTime = 0;
		long postgresProcedureExecTime = 0;
		long main_loop1 = 0, main_loop2 = 0;
		long batchTime2 = 0, batchTime1 = 0;
		
		Statement statement;
		try {
			statement = con.createStatement();
			ResultSet roundCeck = statement.executeQuery("SELECT * FROM app_roundstatus");
			while(roundCeck.next()){
				if (roundCeck.getBoolean("is_running") == false )
					return;
			}
		}
		catch (SQLException ex){
			ex.printStackTrace();
		}

		try {
		statement = con.createStatement();
	 	startTime = System.nanoTime();
		Statement statement2 = con.createStatement();
		
		//lock the tables so that users dont interfere with the update
		con.setAutoCommit(false);
		statement.execute("LOCK TABLE \"PLANET\", app_roundstatus, app_userstatus, app_construction, app_fleet IN ACCESS EXCLUSIVE MODE;");
		
		//update tick number
		ResultSet resultSet = statement.executeQuery("SELECT tick_number FROM app_roundstatus");
		resultSet.next();
		int tick_nr = resultSet.getInt("tick_number");
		System.out.println("Process of tick #" + tick_nr + " has started!");
	
		statement.executeUpdate("UPDATE app_roundstatus SET tick_number = " + (tick_nr + 1) );


		ResultSet TF = statement.executeQuery("SELECT empire_holding_id FROM app_artefacts WHERE name = 'Terraformer' ");
		TF.next();
		int TFA = TF.getInt("empire_holding_id");
		ResultSet TFTF = statement.executeQuery("SELECT ticks_left FROM app_artefacts WHERE name = 'Terraformer' ");
		TFTF.next();
		int TFT = TFTF.getInt("ticks_left");
		ResultSet DU = statement.executeQuery("SELECT empire_holding_id FROM app_artefacts WHERE name = 'Flying Dutchman' ");
		DU.next();
		int FDU = DU.getInt("empire_holding_id");
		ResultSet TFD = statement.executeQuery("SELECT ticks_left FROM app_artefacts WHERE name = 'Flying Dutchman' ");
		TFD.next();
		int FLD = TFD.getInt("ticks_left");
		ResultSet TG = statement.executeQuery("SELECT empire_holding_id FROM app_artefacts WHERE name = 'The General' ");
		TG.next();
		int TGA = TG.getInt("empire_holding_id");
		ResultSet GL = statement.executeQuery("SELECT ticks_left FROM app_artefacts WHERE name = 'The General' ");
		GL.next();
		int GLA = GL.getInt("ticks_left");
		ResultSet TJ = statement.executeQuery("SELECT ticks_left FROM app_artefacts WHERE name = 'Tyrs Justice' ");
		TJ.next();
		int TJA = TJ.getInt("ticks_left");


		
		//update terraformer
		
		if(TFA >= 1){
		    statement.execute("UPDATE app_artefacts SET ticks_left = ticks_left - 1 WHERE name = 'Terraformer';");
		    }
		else{statement.execute("UPDATE app_artefacts SET ticks_left = 1 WHERE name = 'Terraformer';");}
		
		if(TFT == 0){
		    ProcessBuilder pb = new ProcessBuilder("python", "/code/manage.py", "generate_terraformer");
			    Process p = pb.start();
			}
		
		//update dutchman
		
		if(FDU >= 1){
		    statement.execute("UPDATE app_artefacts SET ticks_left = ticks_left - 1 WHERE name = 'Flying Dutchman';");
		    }
		else{statement.execute("UPDATE app_artefacts SET ticks_left = 1 WHERE name = 'Flying Dutchman';");}
		
		if(FLD == 0){
		    ProcessBuilder pb = new ProcessBuilder("python", "/code/manage.py", "generate_dutchman");
			    Process p = pb.start();
			}
		
		//update general
		
		if(GLA >= 1){
		    statement.execute("UPDATE app_artefacts SET ticks_left = ticks_left - 1 WHERE name = 'The General';");
		    }
		
		//update justic
		
		if(TJA >= 1){
		    statement.execute("UPDATE app_artefacts SET ticks_left = ticks_left - 1 WHERE name = 'Tyrs Justice';");
		    }
					
		//update fleet construction time
		statement.execute("UPDATE app_unitconstruction SET ticks_remaining = ticks_remaining - 1;");
		
		//udpate rel timer
		statement.execute("UPDATE app_relations SET relation_remaining_time = relation_remaining_time - 1 WHERE relation_type = 'W';");
		statement.execute("UPDATE app_relations SET relation_remaining_time = relation_remaining_time - 1 WHERE relation_type = 'NC';");
		statement.execute("UPDATE app_relations SET relation_remaining_time = relation_remaining_time - 1 WHERE relation_type = 'C';");
		statement.execute("DELETE FROM app_relations WHERE relation_remaining_time = 0;");
		
		//udpate bot attack
		statement.execute("UPDATE app_botattack SET time = time - 1;");
		statement.execute("DELETE FROM app_botattack WHERE time = 0;");
		
		//update specops time
		statement.execute("UPDATE app_specops SET ticks_left = ticks_left - 1;");
		statement.execute("DELETE FROM app_specops WHERE ticks_left = 0;");
		
		resultSet = statement.executeQuery("SELECT * FROM app_userstatus");
	   	ResultSetMetaData rsmd = resultSet.getMetaData();
	   	ArrayList<String []> columns = new ArrayList<>(rsmd.getColumnCount());
		 
		//put user table into list with hash maps, as we cannot use nested resultSet
	  	for(int i = 1; i <= rsmd.getColumnCount(); i++){
			String [] arr = new String[2];
			arr[0] = rsmd.getColumnName(i);
			arr[1] = rsmd.getColumnClassName(i);
			//System.out.println(Arrays.toString(arr));
			columns.add(arr);
		 }
		 
		 //System.out.println(columns);
		 ArrayList<HashMap<String, Integer>> usersInt = new ArrayList<>();
		 ArrayList<HashMap<String, Long>> usersLong = new ArrayList<>();
		 HashMap<Integer, String> usersRace = new HashMap<>();

		String fleetsDeleteUpdateQuery = "DELETE FROM app_fleet WHERE id = ?";
		PreparedStatement fleetsDeleteUpdateStatement = con.prepareStatement(fleetsDeleteUpdateQuery); 

		PreparedStatement userStatusUpdateStatement = con.prepareStatement(userStatusUpdateQuery); //mass update, much faster

		String specopIncomeUpdateQuery = "UPDATE app_userstatus SET" +
			" energy_specop_effect = energy_specop_effect + ? , "+	 //1	
			" energy_income = energy_income + ? , "+	 //2
			" energy = energy + ? "+ //3
			" WHERE id = ? ;"  ; //4
					
		PreparedStatement userIncomeUpdateStatement = con.prepareStatement(specopIncomeUpdateQuery);

		 //loop over users to get their stats
		while(resultSet.next()){
			if(resultSet.getLong("networth") == 0){
				//System.out.println("networth was null");
				continue;
			}

			//check if the players empire is null
			resultSet.getInt("empire_id");
		 	if (resultSet.wasNull()){
		   		continue;
			}
			int id = resultSet.getInt("id");
			String race = resultSet.getString("race");
			usersRace.put(id, race);
			
			HashMap<String,Integer> userIntValues = new HashMap<>(columns.size());
			HashMap<String,Long> userLongValues = new HashMap<>(columns.size());
			for(String[] col : columns) {
				if(col[1].equals("java.lang.Integer"))
			    		userIntValues.put(col[0], resultSet.getInt(col[0]));
				else if(col[1].equals("java.lang.Long"))
			    		userLongValues.put(col[0], resultSet.getLong(col[0]));
			}
			usersInt.add(userIntValues);
			usersLong.add(userLongValues);
		}
		
		
		UpdateNews updateNews = new UpdateNews(con, tick_nr);
		UpdateFleets updateFleets = new UpdateFleets(con, updateNews);
		
		UpdatePlanets userPlanetsUpdate = new UpdatePlanets(con);
					
		//loops over users to uodate their stats and planets --main loop!
		main_loop1 = System.nanoTime();
		for(int j = 0; j < usersInt.size(); j++){

			HashMap<String,Integer> userIntValues = usersInt.get(j);
			HashMap<String,Long> userLongValues  = usersLong.get(j);
			int userID = userIntValues.get("user_id");
			int empireID = userIntValues.get("empire_id");
			userStatusUpdateStatement.setInt(63, userID);
			String race = usersRace.get(userID);
			HashMap<String, Double> race_info = race_info_list.get(race);
			long networth = 1;
			
			//set initial news flags
			userStatusUpdateStatement.setInt(56, userIntValues.get("construction_flag"));
			userStatusUpdateStatement.setInt(57, userIntValues.get("economy_flag"));
			userStatusUpdateStatement.setInt(58, userIntValues.get("military_flag"));
			
			//create news updating
			updateFleets.addNewUser(userID, empireID, tick_nr, userStatusUpdateStatement);
			
			//update built fleets
			updateFleets.updateFleetBuild();

			if (updateFleets.getTotalBuiltUnits() > 0)
				userStatusUpdateStatement.setInt(56, 1);	
			
			int militaryFlag = userIntValues.get("military_flag");

			//update built fleets news 
			Statement statement3 = con.createStatement();
			ResultSet portalstSet = statement3.executeQuery("SELECT * FROM \"PLANET\" WHERE portal = TRUE AND owner_id = " + userID );
			
			 //this may be quite slow with a lot of portals and planets, could optimize this later
			LinkedList<Planet> portals = new LinkedList<>();

			while(portalstSet.next()){
				Planet planet = new Planet(portalstSet.getInt("x"), portalstSet.getInt("y"), portalstSet.getInt("i"));
				portals.add(planet);
			}
			ResultSet vpportalstSet = statement.executeQuery("SELECT * FROM \"PLANET\" INNER JOIN app_specops ON \"PLANET\".id = planet_id WHERE name = 'Vortex Portal' AND app_specops.user_to_id = " + userID);
			while(vpportalstSet.next()){
				Planet planet = new Planet(vpportalstSet.getInt("x"), vpportalstSet.getInt("y"), vpportalstSet.getInt("i"));
				portals.add(planet);
			}
			//update mooving fleets
			updateFleets.updateMoovingFleets(portals, militaryFlag, race_info);
			
			//calculate various stuff for and from users planets
			userPlanetsUpdate.updateUserPlanets(userID, empireID, userIntValues, race_info, portals, updateNews, userStatusUpdateStatement);

			//update planets
			userStatusUpdateStatement.setInt(55, userPlanetsUpdate.getNumPlanets());
			
			//update population
			userStatusUpdateStatement.setLong(4, userPlanetsUpdate.getPopulation());
			
			//Enlightenment spell - increases productions
			long energy_specop_effect1 = 0;
			
			long mineralProduction = userPlanetsUpdate.getResourceProduction(0);
			long crystalProduction = userPlanetsUpdate.getResourceProduction(1);
			long ectroliumProduction = userPlanetsUpdate.getResourceProduction(2);
			double enlightenmentResearchFactor = 1;
			double enlightenmentEnergyFactor = 0;
			
			ResultSet operationSet = statement3.executeQuery("SELECT * FROM app_specops WHERE name = 'Enlightenment' AND user_to_id = " + userID);
			
			while (operationSet.next()){
				if (operationSet.getString("extra_effect").equals("Energy")){
					enlightenmentEnergyFactor = operationSet.getDouble("specop_strength") /100;
				}
				else if (operationSet.getString("extra_effect").equals("Mineral")){
					mineralProduction *= (1 + operationSet.getDouble("specop_strength") /100);
				}
				else if (operationSet.getString("extra_effect").equals("Crystal")){
					crystalProduction *= (1 + operationSet.getDouble("specop_strength") /100);
				}
				else if (operationSet.getString("extra_effect").equals("Ectrolium")){
					ectroliumProduction *= (1 + operationSet.getDouble("specop_strength") /100);
				}
				else if (operationSet.getString("extra_effect").equals("Research")){
					enlightenmentResearchFactor *= (1 + operationSet.getDouble("specop_strength") /100);
				}
			}
			
			//update reseach
			int artibonus = 0;
			double racebonus = 0;
			double popcount = 6000;
			if (race.equals("FH"))
				racebonus = 1.0;
			if (race.equals("JK")){
				racebonus = 1.0;
				popcount = 10000;}
			
			//Research laboratory artefact resarch
			Statement statement4 = con.createStatement();
			double research_modifier = 1.0;
			ResultSet artefactSet = statement4.executeQuery("SELECT * FROM app_artefacts WHERE name = 'Research Laboratory' AND empire_holding_id = " + empireID);
			while (artefactSet.next()){
				research_modifier = 1.0 + artefactSet.getInt("effect1") / 100.0;
			}

			long totalRcPoints = 0;
			for(int i = 0; i < researchNames.length; i++){				
				long rc = (long) (
				userLongValues.get(researchNames[i][0]) +
				research_modifier * (enlightenmentResearchFactor * 1.2 * race_info.get(researchNames[i][1])  * userIntValues.get(researchNames[i][2])
				* (userPlanetsUpdate.getResearchProduction() + userLongValues.get("current_research_funding")/100 + 
				(racebonus * userPlanetsUpdate.getPopulation() / popcount) )  / 100
				));			
				
				double raceMax = race_info.getOrDefault(researchNames[i][3], 200.0);
				
				long rpoints = 0;
				ResultSet rabbitSet = statement4.executeQuery("SELECT * FROM app_artefacts WHERE name = 'Rabbit Theorum' AND empire_holding_id = " + empireID);
			    while (rabbitSet.next()){
			        if (i == 4){
				    rpoints = (long) (research_modifier * (enlightenmentResearchFactor * 1.2 * race_info.get(researchNames[i][1])  * userIntValues.get(researchNames[i][2])
				    * (userPlanetsUpdate.getResearchProduction() + userLongValues.get("current_research_funding")/100 + 
				    (racebonus * userPlanetsUpdate.getPopulation() / popcount) )  / 100
				    ));
				    rc += rpoints;}
			    }
				
				long ppoints = 0;
				ResultSet quantumSet = statement4.executeQuery("SELECT * FROM app_artefacts WHERE name = 'Playboy Quantum' AND empire_holding_id = " + empireID);
			    while (quantumSet.next()){
				    if (i == 7){
				    raceMax += 100;
				    ppoints = (long) (research_modifier * (enlightenmentResearchFactor * 1.2 * race_info.get(researchNames[i][1])  * userIntValues.get(researchNames[i][2])
				    * (userPlanetsUpdate.getResearchProduction() + userLongValues.get("current_research_funding")/100 + 
				    (racebonus * userPlanetsUpdate.getPopulation() / popcount) )  / 100
				    ));
				    rc += ppoints/2;}
			    }
				
				rc = Math.max(0, rc);
				totalRcPoints += rc;
				userStatusUpdateStatement.setLong(15 + i, rc);
				
				long nw = userLongValues.get("networth");
				int rcPercent = (int) Math.floor(raceMax * (1.0 - Math.exp(rc / (-10.0 * nw))));
				if(raceMax == 100){
					rcPercent = (int) Math.min(100, Math.floor(200 * (1.0 - Math.exp(rc / (-10.0 * nw)))));}
				int currPercent = (int) (userIntValues.get(researchNames[i][4]));			
				
				if (rcPercent > currPercent )
					userStatusUpdateStatement.setInt(24 + i, currPercent + 1);
				else if (rcPercent < currPercent )
					userStatusUpdateStatement.setInt(24 + i, currPercent - 1);
				else
					userStatusUpdateStatement.setInt(24 + i, currPercent);
			}

			long current_research_funding  = userLongValues.get("current_research_funding") * 9 / 10;

			//update energy income
			//race_special_solar_15
			long energyProduction = (long)(userPlanetsUpdate.getEnergyProduction(0));
			energyProduction += userPlanetsUpdate.getEnergyProduction(1);
			double energyRaceFactor = race_info.get("energy_production");
			double energyResearchFactor = (1 + userIntValues.get("research_percent_energy")/100.0);
			energyProduction = (long) (energyProduction * energyRaceFactor * energyResearchFactor);	
			
			//ether gardens artefact energy
			artefactSet = statement4.executeQuery("SELECT * FROM app_artefacts WHERE name = 'Ether Gardens' AND empire_holding_id = " + empireID);
			while (artefactSet.next()){
				energyProduction *= 1.0 + artefactSet.getInt("effect1") / 100.0;
			}
			
			//enlightnment energy
			if (enlightenmentEnergyFactor > 0){
				energy_specop_effect1 = (long)(enlightenmentEnergyFactor * energyProduction);
			}

			//energy decay
			long lastTickEnergy = userLongValues.get("energy");
			long energyDecay = (long) (Math.max(0,lastTickEnergy * energy_decay_factor));
			userStatusUpdateStatement.setLong(33, energyDecay);
			
			//energy interest
			long energy_interest = (long) (userLongValues.get("energy") * race_info.getOrDefault("race_special_resource_interest", 0.0));
			if (energy_interest >= energyProduction)
				energy_interest = energyProduction;
			userStatusUpdateStatement.setLong(42, energy_interest);
		
			//buildings upkeep
			long buildings_upkeep = 
            (long) (userPlanetsUpdate.getTotalBuildings(0) * upkeep_solar_collectors +
            userPlanetsUpdate.getTotalBuildings(1) * upkeep_fission_reactors * (energyResearchFactor/2) +
            userPlanetsUpdate.getTotalBuildings(2) * upkeep_mineral_plants +
            userPlanetsUpdate.getTotalBuildings(3) * upkeep_crystal_labs +
            userPlanetsUpdate.getTotalBuildings(4) * upkeep_refinement_stations +
            userPlanetsUpdate.getTotalBuildings(5) * upkeep_cities +
            userPlanetsUpdate.getTotalBuildings(6) * upkeep_research_centers +
            userPlanetsUpdate.getTotalBuildings(7) * upkeep_defense_sats +
            userPlanetsUpdate.getTotalBuildings(8) * upkeep_shield_networks);
            
            ResultSet ENG = statement.executeQuery("SELECT empire_holding_id FROM app_artefacts WHERE name = 'Engineer' ");
		    ENG.next();
		    int ENGA = ENG.getInt("empire_holding_id");
		    
		    ResultSet ENS = statement.executeQuery("SELECT empire_holding_id FROM app_artefacts WHERE name = 'Engineers Son' ");
		    ENS.next();
		    int ENSA = ENS.getInt("empire_holding_id");
            
            ResultSet engineerSet = statement4.executeQuery("SELECT * FROM app_artefacts WHERE name = 'Engineer' AND empire_holding_id = " + empireID);
            while (engineerSet.next()){
                if(ENGA == ENSA){
                buildings_upkeep *= 0.8;
                }
                else{
                buildings_upkeep *= 0.9;
                }
            }
            
			userStatusUpdateStatement.setLong(34, buildings_upkeep);
			
			//get unit amounts
			long [] unitsSums = new long[total_units];
			statement2 = con.createStatement();		
			for(int z = 0; z < unit_names.length; z++){
				String s = unit_names[z];
				String query = "SELECT SUM(" + s + ") FROM app_fleet WHERE owner_id = " + userID;
				ResultSet result = statement2.executeQuery(query);
				result.next();
				unitsSums[z] += result.getLong("sum"); 
			}
			
			//units upkeep
			long units_upkeep = 0;
			for(int i = 0; i < total_units; i++) {
				units_upkeep += (long)(units_upkeep_costs[i] * unitsSums[i]);
				networth += (long)(unitsSums[i] * units_nw[i]);
			}
			
			//general with might
			
			ResultSet GEN = statement.executeQuery("SELECT empire_holding_id FROM app_artefacts WHERE name = 'The General' ");
		    GEN.next();
		    int GENM = GEN.getInt("empire_holding_id");
			
			//Military might artefact
			artefactSet = statement4.executeQuery("SELECT * FROM app_artefacts WHERE name = 'Military Might' AND empire_holding_id = " + empireID);
			while (artefactSet.next()){
				if (GENM == empireID){
					units_upkeep *= 1.0 - (artefactSet.getInt("effect1")*2) / 100.0;
				}
				else{
				units_upkeep *= 1.0 - artefactSet.getInt("effect1") / 100.0;
				}
			}
			
			userStatusUpdateStatement.setLong(35, units_upkeep);
			
			//portals upkeep 
			int portals_upkeep = (int)(Math.max(0, (Math.pow(Math.max(1, userPlanetsUpdate.getTotalBuildings(9)) - 1, 1.2736) * 10000.0 /
								(1.0 + userIntValues.get("research_percent_portals")/100.0))));
			userStatusUpdateStatement.setInt(37, portals_upkeep);

			//population upkeep reduction		
			long population_upkeep_reduction = userPlanetsUpdate.getPopulation() / 350;
			population_upkeep_reduction = Math.min(population_upkeep_reduction, buildings_upkeep + units_upkeep + portals_upkeep);
			
			//Darwinism artefact
			artefactSet = statement4.executeQuery("SELECT * FROM app_artefacts WHERE name = 'Darwinism' AND empire_holding_id = " + empireID);
			while (artefactSet.next()){
				population_upkeep_reduction = userPlanetsUpdate.getPopulation() / 315;
			}
			
			userStatusUpdateStatement.setLong(36, population_upkeep_reduction);
			


			//minerals
		    int mineral_production = (int) (race_info.get("mineral_production") * mineralProduction);
			
			//Mirny mine artefact minerals
			artefactSet = statement4.executeQuery("SELECT * FROM app_artefacts WHERE name = 'Mirny Mine' AND empire_holding_id = " + empireID);
			while (artefactSet.next()){
				mineral_production *= 1.0 + artefactSet.getInt("effect1") / 100.0;
			}
			
		    int mineral_decay = 0;
		    int mineral_interest = (int) (userLongValues.get("minerals") * race_info.getOrDefault("race_special_resource_interest", 0.0));
		    if (mineral_interest >= mineral_production)
				mineral_interest = mineral_production;
			//spoil op modifier
			operationSet = statement3.executeQuery("SELECT * FROM app_specops WHERE name = 'Spoil Resources' AND user_to_id = " + userID);
			
			while(operationSet.next()){
				double factor = operationSet.getFloat("specop_strength")/100;
				
				mineral_decay += (int) (userLongValues.get("minerals") * factor);
			}
		    int mineral_income = mineral_production - mineral_decay + mineral_interest;
		    userStatusUpdateStatement.setInt(38, mineral_production);
		    userStatusUpdateStatement.setInt(43, mineral_interest);
		    userStatusUpdateStatement.setInt(47, mineral_income);
			userStatusUpdateStatement.setInt(61, mineral_decay);

		    //crystals
    	    int crystal_production = (int) (race_info.get("crystal_production") *  crystalProduction);
			
			//Crystal synthesis artefact скныефды
			artefactSet = statement4.executeQuery("SELECT * FROM app_artefacts WHERE name = 'Crystal Synthesis' AND empire_holding_id = " + empireID);
			while (artefactSet.next()){
				crystal_production *= 1.0 + artefactSet.getInt("effect1") / 100.0;
			}
			
    	    int crystal_decay = (int) (Math.max(0.0,userLongValues.get("crystals") * crystal_decay_factor));
			
			artefactSet = statement4.executeQuery("SELECT * FROM app_artefacts WHERE name = 'Crystal Recharger' AND empire_holding_id = " + empireID);
			while (artefactSet.next()){
				crystal_decay *= 0.25;
			}
			
    	    int crystal_interest = (int) (userLongValues.get("crystals") * race_info.getOrDefault("race_special_resource_interest", 0.0));
    	    if (crystal_interest >= crystal_production)
				crystal_interest = crystal_production;
    	    int crystal_income = crystal_production - crystal_decay + crystal_interest;
    	    userStatusUpdateStatement.setInt(39, crystal_production);
    	    userStatusUpdateStatement.setInt(40, crystal_decay);
    	    userStatusUpdateStatement.setInt(44, crystal_interest);
    	    userStatusUpdateStatement.setInt(48, crystal_income);
			
    	    //ectrolium		    	    
    	    int ectrolium_production = (int) (race_info.get("ectrolium_production") * ectroliumProduction);
			
			//Foohon technology artefact ectrolium
			artefactSet = statement4.executeQuery("SELECT * FROM app_artefacts WHERE name = 'Foohon Technology' AND empire_holding_id = " + empireID);
			while (artefactSet.next()){
				ectrolium_production *= 1.0 + artefactSet.getInt("effect1") / 100.0;
			}
			
    	    int ectrolium_decay = 0;
    	    int ectrolium_interest =(int) (userLongValues.get("ectrolium") * race_info.getOrDefault("race_special_resource_interest", 0.0));
    	    if (ectrolium_interest >= ectrolium_production)
				ectrolium_interest = ectrolium_production;
    	    
			//spoil op modifier
			operationSet = statement3.executeQuery("SELECT * FROM app_specops WHERE name = 'Spoil Resources' AND user_to_id = " + userID);
			
			while(operationSet.next()){
				double factor = operationSet.getFloat("specop_strength")/100;
				
				ectrolium_decay += (int) (userLongValues.get("ectrolium") * factor);
			}
			
			int ectrolium_income = ectrolium_production - ectrolium_decay + ectrolium_interest;
    	    userStatusUpdateStatement.setInt(41, ectrolium_production);
    	    userStatusUpdateStatement.setInt(45, ectrolium_interest);
    	    userStatusUpdateStatement.setInt(49, ectrolium_income);
			userStatusUpdateStatement.setInt(62, ectrolium_decay);
			
			
			
			//hack mainframe op modifier
			operationSet = statement3.executeQuery("SELECT * FROM app_specops WHERE name = 'Hack mainframe' AND user_to_id = " + userID);
			
			
			
			while(operationSet.next()){
				long energyProductionTmp = energyProduction;
				double factor = operationSet.getFloat("specop_strength")/100;
				double factor2 = operationSet.getFloat("specop_strength2")/100;
				
				long subtractEnergy = (long) (factor * energyProductionTmp); 
				energy_specop_effect1 -= subtractEnergy;
				energyProductionTmp -= energy_specop_effect1;
				long energy_specop_effect2 = (long) (subtractEnergy * factor2);
				userIncomeUpdateStatement.setLong(1, energy_specop_effect2);
				userIncomeUpdateStatement.setLong(2, energy_specop_effect2);
				userIncomeUpdateStatement.setLong(3, energy_specop_effect2);
				userIncomeUpdateStatement.setLong(4, operationSet.getInt("user_from_id"));
				userIncomeUpdateStatement.addBatch();
			}
			
			//energy_specop_effect
			userStatusUpdateStatement.setLong(60, energy_specop_effect1); 
			userStatusUpdateStatement.setLong(32, energyProduction);
			
			//update resources income
			//energy

			long energy_income = (energyProduction + energy_interest + population_upkeep_reduction + energy_specop_effect1) - (energyDecay + units_upkeep + buildings_upkeep + portals_upkeep) ;

			
			userStatusUpdateStatement.setLong(46, energy_income);
    	    
    	    //update total resources
    	    userStatusUpdateStatement.setLong(50, Math.max(0, userLongValues.get("energy") + energy_income));
    	    userStatusUpdateStatement.setLong(51, Math.max(0, userLongValues.get("minerals") + mineral_income));
    	    userStatusUpdateStatement.setLong(52, Math.max(0,userLongValues.get("crystals") + crystal_income));
    	    userStatusUpdateStatement.setLong(53, Math.max(0,userLongValues.get("ectrolium") + ectrolium_income));
			

			//decay
			
			if( Math.max(0, userLongValues.get("energy") + energy_income) > 0){
				int fr = Math.min(userIntValues.get("fleet_readiness")+2, userIntValues.get("fleet_readiness_max"));
				userStatusUpdateStatement.setInt(1, fr);
				int pr = Math.min(userIntValues.get("psychic_readiness")+2, userIntValues.get("psychic_readiness_max"));
				userStatusUpdateStatement.setInt(2, pr);
				int ar = Math.min(userIntValues.get("agent_readiness")+2, userIntValues.get("agent_readiness_max"));
				userStatusUpdateStatement.setInt(3, ar);
			}
			else{
				int fr = Math.max(userIntValues.get("fleet_readiness")-3, -100);
				userStatusUpdateStatement.setInt(1, fr);
				int pr = Math.max(userIntValues.get("psychic_readiness")-3, -100);
				userStatusUpdateStatement.setInt(2, pr);
				int ar = Math.max(userIntValues.get("agent_readiness")-3, -100);
				userStatusUpdateStatement.setInt(3, ar);
				//fleets also decya, 2% a tick
				updateFleets.updateDecayedFleet();
			}
			if((tick_nr % 2) == 0){
			if( Math.max(0, userLongValues.get("energy") + energy_income) > 0){
			artefactSet = statement4.executeQuery("SELECT * FROM app_artefacts WHERE name = 'Churchills Brandy' AND empire_holding_id = " + empireID);
			while (artefactSet.next()){
				int fr = Math.min(userIntValues.get("fleet_readiness")+3, userIntValues.get("fleet_readiness_max"));
				userStatusUpdateStatement.setInt(1, fr);
			}}}

			//update research funding
			
			long rc_funding = (long) Math.max(0, userLongValues.get("current_research_funding") * 0.9 ) ;
			
			artefactSet = statement4.executeQuery("SELECT * FROM app_artefacts WHERE name = 'The Recycler' AND empire_holding_id = " + empireID);
			while (artefactSet.next()){
				rc_funding += (energyDecay * (0.005 + userIntValues.get("research_percent_tech")/200.0));
			}
			
			userStatusUpdateStatement.setLong(23, rc_funding);
			
			//update total buildings
			int total_buildings = 0;
			for(int i = 5, k = 0; i < 15; i++, k++){
				userStatusUpdateStatement.setInt(i, userPlanetsUpdate.getTotalBuildings(k));
				total_buildings += userPlanetsUpdate.getTotalBuildings(k);
			}
			
			userStatusUpdateStatement.setInt(59, total_buildings);
			userStatusUpdateStatement.setInt(63, userID);
			
			//update networth
			networth += userPlanetsUpdate.getNetworth();
			networth += userPlanetsUpdate.getPopulation() * 0.0005;
			networth += (0.001 * totalRcPoints);
			userStatusUpdateStatement.setLong(54, networth);	

			//fleets update
			updateFleets.updateFleetsMerge();
			updateFleets.updateStationedFleets();
			updateFleets.updatePhantomDecay(networth);
			
			//this must be the last update!
			userStatusUpdateStatement.addBatch();
		}
		main_loop2 = System.nanoTime();
		
		batchTime1 = System.nanoTime();
	
		//execute update planets for all users
		userPlanetsUpdate.UpdatePlanetsExecute();

		//update users
		userStatusUpdateStatement.executeBatch();
		
		//update income from specops
		userIncomeUpdateStatement.executeBatch();
		
		//update building news	
		updateNews.executeNews();
		
		//update building fleets
		updateFleets.executeFleetsUpdate();
		
		//delete returned fleets
		fleetsDeleteUpdateStatement.executeBatch();
		
		//update empire ranks
		String updateEmpireRanks = 
		"UPDATE app_empire "+
		"SET numplayers = GroupedUserTable.num_players , "+
			"planets = GroupedUserTable.sum_planets, "+
			"networth = sum_networth "+
		"FROM ( "+
			"SELECT empire_id, COUNT(id) as num_players ,SUM(num_planets) as sum_planets, SUM(networth) as sum_networth "+
			"FROM app_userstatus GROUP BY empire_id ) AS GroupedUserTable "+
		"WHERE "+
			"app_empire.id = GroupedUserTable.empire_id;";
		statement.execute(updateEmpireRanks);
		
		//purge old news
		String deletePersonalNews = "DELETE FROM app_news WHERE is_personal_news = false AND " + tick_nr + "  - tick_number > " + news_delete_ticks + " ;"; 
		String deleteEmpireNews =  "DELETE FROM app_news WHERE is_personal_news = true AND is_read = true AND "+
									tick_nr + "  - tick_number > " + news_delete_ticks + " ;"; 
															
		statement.execute(deletePersonalNews);		
		statement.execute(deleteEmpireNews);	

		//delete elapsed fleet construction
		statement.execute("DELETE FROM app_unitconstruction WHERE ticks_remaining = 0;");
		
		//delete empty fleets
		updateFleets.deleteEmptyFleets();
		
		batchTime2 = System.nanoTime();
		
		con.commit();
		}
		catch (Exception e) {
		   try{
				con.rollback();
			}
			catch (SQLException ex){
				ex.printStackTrace();
			}
			
			System.out.println("exception " +  e.getMessage());
			e.printStackTrace();
		}
		
		//process ops
		
		long python_script1 = System.nanoTime();
		try{
			ProcessBuilder pb = new ProcessBuilder("python", "/code/manage.py", "process_ops");
			Process p = pb.start();

		}
		catch (Exception e){
			System.out.println("Exception: " +  e.getMessage());
		}
		
		
		
		long endTime = System.nanoTime();
		
		Clock clock = Clock.systemDefaultZone();
		Instant instant = clock.instant();
		System.out.println("Tick completion time: " + instant);	
		System.out.println("Execute postgres population update procedure: " + (double)(postgresProcedureExecTime)/1_000_000_000.0 + " sec.");
		System.out.println("batch executions: " + (double)(batchTime2 - batchTime1)/1_000_000_000.0 + " sec.");
		System.out.println("Main loop: " + (double)(main_loop2-main_loop1)/1_000_000_000.0 + " sec.");
		System.out.println("Python script process_ops time: " + (double)(python_script1-main_loop2)/1_000_000_000.0 + " sec.");
		System.out.println("Total time: " + (double)(endTime-startTime)/1_000_000_000.0 + " sec.");
		System.out.println("");
		

	}
}
