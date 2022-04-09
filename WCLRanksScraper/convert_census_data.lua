#!/usr/bin/env lua
server_name, faction = ...
print(server_name)
lunajson = require 'lunajson'

function firstToUpper(str)
    return (str:gsub("^%l", string.upper))
end

function DeepPrint (e, pkey, of)
    for k,v in pairs(e) do
        if type(v) == "table" then
          DeepPrint(v, k, of)
        else 
			if v == 70 then -- Only print names of characters that are at max level
				print(pkey)
			end
        end
    end
end

dofile "/mnt/c/Program Files (x86)/World of Warcraft/_classic_/WTF/Account/CARLSVENS/SavedVariables/CensusPlusTBC.lua"
target_file = io.open("targets.json", "r")
j = lunajson.decode(target_file:read("*a"))
for k,v in pairs(CensusPlus_Database["Servers"]) do
	server = string.gsub(k, ".*_(%w+)$", "%1")
	if server == firstToUpper(server_name) then
		DeepPrint(v[firstToUpper(faction)], NULL, of)
	end
end
