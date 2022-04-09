local WP_TargetName
local WP_MouseoverName

local WP_ShowPrintOnClick = true
local _G = getfenv(0)
local WCLRanks = _G.LibStub("AceAddon-3.0"):NewAddon("WCLRanks", "AceTimer-3.0")


local function expand(name)

    local switch = {
        ["K"] = function()
            return "Karazhan"
        end,
        ["Z"] = function()
            return "Zul'Aman"
        end,
        ["G"] = function()
            return "Gruul/Magtheridon"
        end,
        ["T"] = function()
            return "SSC/TK"
        end,
        ["H"] = function()
            return "BT/Hyjal"
        end,
        ["B"] = function()
            return " Server Rank No."
        end,
        ["D"] = function()
            return " Region Rank NO."
        end,
        ["A"] = function()
            return "|cFFE5CC80"
        end,
        ["S"] = function()
            return "|cFFE26880"
        end,
        ["L"] = function()
            return "|cFFFF8000"
        end,
        ["N"] = function()
            return "|cFFBE8200"
        end,
        ["E"] = function()
            return "|cFFA335EE"
        end,
        ["R"] = function()
            return "|cFF0070FF"
        end,
        ["U"] = function()
            return "|cFF1EFF00"
        end,
        ["C"] = function()
            return "|cFF666666"
        end
    }

    local out = {}
    local idx = 1
    local str = ""
    local max = strlen(name)
    local inner_loop = 0
    for j=1,max do
            ts = strsub(name,j,j)

	    if ts == "(" then
		    inner_loop = 1
	    end

	    if inner_loop == 1 then
		    str = str .. ts
	    elseif ts == "|" then
		    out[idx] = str
		    idx = idx + 1
		    str = ""
	    else
            	local f = switch[ts]
            	if f then
                	str = str .. f()
            	else
                	str = str .. ts
            	end
	    end

	    if ts == ")" then
		    inner_loop = 0
	    end
    end
    return out
end

local function cut_str(str)
	if str ~= nil then
		local s1,s2,s3 = strsplit("%",str);
		if s1 ~= nil then
			s1 = s1 .. "%"
			if s2 ~= nil then
				s1 = s1 .. s2 .. "%"
			end
			return s1
		end
	end
	return nil
end


local function load_data(tname)
	if type(WP_Database) ~= "table" then
		return nil
	end
	if WP_Database[tname] then
		return expand(WP_Database[tname])
	end
	return nil
end

hooksecurefunc("ChatFrame_OnHyperlinkShow", function(chatFrame, link, text, button)
if (IsModifiedClick("CHATLINK")) then
  if (link and button) then
    local args = {};
    for v in string.gmatch(link, "[^:]+") do
      table.insert(args, v);
    end
		if (args[1] and args[1] == "player") then
			args[2] = Ambiguate(args[2], "short")
			WP_TargetName = args[2]
			if WP_ShowPrintOnClick == true then
				dstr_array = load_data(WP_TargetName)
				if dstr_array then
					for i, dstr in ipairs(dstr_array) do
						DEFAULT_CHAT_FRAME:AddMessage('WCL ' .. WP_TargetName .. ': ' .. dstr, 255, 209, 0)
					end
				end
			end
		end
	end
end
end)

local function printInfo(self)
	print("|cFFFFFF00WCL-" .. self.value)
end

hooksecurefunc("UnitPopup_ShowMenu", function(dropdownMenu, which, unit, name, userData)

	WP_TargetName = dropdownMenu.name

	if (UIDROPDOWNMENU_MENU_LEVEL > 1) then
	return
	end

	local dstr_array = load_data(WP_TargetName)

	if dstr and UnitExists(unit) and UnitIsPlayer(unit) then
		local info = UIDropDownMenu_CreateInfo()
		info.text = 'WCL: ' .. dstr_array[1]
		info.owner = which
		info.notCheckable = 1
		info.func = printInfo
		info.value = WP_TargetName .. ": " .. dstr
		UIDropDownMenu_AddButton(info)
	end

end)

function WCLRanks:InitCode()
	GameTooltip:HookScript("OnTooltipSetUnit", function(self)
		local _, unit = self:GetUnit()
		local dstr = ""
		if UnitExists(unit) and UnitIsPlayer(unit) then
			WP_MouseoverName = UnitName(unit)
			dstr_array = load_data(WP_MouseoverName)
			if dstr_array then
				for i, dstr in ipairs(dstr_array) do
					GameTooltip:AddLine(dstr, 255, 209, 0)
				end
			end
			GameTooltip:Show()
		end
	end)
end


local Addon_EventFrame = CreateFrame("Frame")
Addon_EventFrame:RegisterEvent("ADDON_LOADED")
Addon_EventFrame:SetScript("OnEvent",
	function(self, event, addon)
		if addon == "WCLRanks" then
			WP_Database = WP_Database or {}
			WP_Database_1 = WP_Database_1 or {}
			WP_Database_2 = WP_Database_2 or {}
			WP_Database_3 = WP_Database_3 or {}
			WCLRanks:ScheduleTimer("InitCode", 5)
		end
end)


local Chat_EventFrame = CreateFrame("Frame")
Chat_EventFrame:RegisterEvent("CHAT_MSG_SYSTEM")
Chat_EventFrame:SetScript("OnEvent",
	function(self, event, message)
	local name

	name = Deformat(message, _G.WHO_LIST_FORMAT)
	if name then
		dstr_array = load_data(name)
		if dstr_array then
			for i, dstr in ipairs(dstr_array) do
				print("|cFFFFFF00WCL " .. name .. ":" .. dstr )
			end
		end
	end
end)


-- a dictionary of format to match entity
local FORMAT_SEQUENCES = {
    ["s"] = ".+",
    ["c"] = ".",
    ["%d*d"] = "%%-?%%d+",
    ["[fg]"] = "%%-?%%d+%%.?%%d*",
    ["%%%.%d[fg]"] = "%%-?%%d+%%.?%%d*",
}

-- a set of format sequences that are string-based, i.e. not numbers.
local STRING_BASED_SEQUENCES = {
    ["s"] = true,
    ["c"] = true,
}

local cache = setmetatable({}, {__mode='k'})
-- generate the deformat function for the pattern, or fetch from the cache.
local function get_deformat_function(pattern)
    local func = cache[pattern]
    if func then
        return func
    end

    -- escape the pattern, so that string.match can use it properly
    local unpattern = '^' .. pattern:gsub("([%(%)%.%*%+%-%[%]%?%^%$%%])", "%%%1") .. '$'

    -- a dictionary of index-to-boolean representing whether the index is a number rather than a string.
    local number_indexes = {}

    -- (if the pattern is a numbered format,) a dictionary of index-to-real index.
    local index_translation = nil

    -- the highest found index, also the number of indexes found.
	local highest_index
    if not pattern:find("%%1%$") then
        -- not a numbered format

        local i = 0
        while true do
            i = i + 1
            local first_index
            local first_sequence
            for sequence in pairs(FORMAT_SEQUENCES) do
                local index = unpattern:find("%%%%" .. sequence)
                if index and (not first_index or index < first_index) then
                    first_index = index
                    first_sequence = sequence
                end
            end
            if not first_index then
                break
            end
            unpattern = unpattern:gsub("%%%%" .. first_sequence, "(" .. FORMAT_SEQUENCES[first_sequence] .. ")", 1)
            number_indexes[i] = not STRING_BASED_SEQUENCES[first_sequence]
        end

        highest_index = i - 1
    else
        -- a numbered format

        local i = 0
		while true do
		    i = i + 1
			local found_sequence
            for sequence in pairs(FORMAT_SEQUENCES) do
				if unpattern:find("%%%%" .. i .. "%%%$" .. sequence) then
					found_sequence = sequence
					break
				end
			end
			if not found_sequence then
				break
			end
			unpattern = unpattern:gsub("%%%%" .. i .. "%%%$" .. found_sequence, "(" .. FORMAT_SEQUENCES[found_sequence] .. ")", 1)
			number_indexes[i] = not STRING_BASED_SEQUENCES[found_sequence]
		end
        highest_index = i - 1

		i = 0
		index_translation = {}
		pattern:gsub("%%(%d)%$", function(w)
		    i = i + 1
		    index_translation[i] = tonumber(w)
		end)
    end

    if highest_index == 0 then
        cache[pattern] = do_nothing
    else
        --[=[
            -- resultant function looks something like this:
            local unpattern = ...
            return function(text)
                local a1, a2 = text:match(unpattern)
                if not a1 then
                    return nil, nil
                end
                return a1+0, a2
            end

            -- or if it were a numbered pattern,
            local unpattern = ...
            return function(text)
                local a2, a1 = text:match(unpattern)
                if not a1 then
                    return nil, nil
                end
                return a1+0, a2
            end
        ]=]

        local t = {}
        t[#t+1] = [=[
            return function(text)
                local ]=]

        for i = 1, highest_index do
            if i ~= 1 then
                t[#t+1] = ", "
            end
            t[#t+1] = "a"
            if not index_translation then
                t[#t+1] = i
            else
                t[#t+1] = index_translation[i]
            end
        end

        t[#t+1] = [=[ = text:match(]=]
        t[#t+1] = ("%q"):format(unpattern)
        t[#t+1] = [=[)
                if not a1 then
                    return ]=]

        for i = 1, highest_index do
            if i ~= 1 then
                t[#t+1] = ", "
            end
            t[#t+1] = "nil"
        end

        t[#t+1] = "\n"
        t[#t+1] = [=[
                end
                ]=]

        t[#t+1] = "return "
        for i = 1, highest_index do
            if i ~= 1 then
                t[#t+1] = ", "
            end
            t[#t+1] = "a"
            t[#t+1] = i
            if number_indexes[i] then
                t[#t+1] = "+0"
            end
        end
        t[#t+1] = "\n"
        t[#t+1] = [=[
            end
        ]=]

        t = table.concat(t, "")

        -- print(t)

        cache[pattern] = assert(loadstring(t))()
    end

    return cache[pattern]
end

function Deformat(text, pattern)
    if type(text) ~= "string" then
        error(("Argument #1 to `Deformat' must be a string, got %s (%s)."):format(type(text), text), 2)
    elseif type(pattern) ~= "string" then
        error(("Argument #2 to `Deformat' must be a string, got %s (%s)."):format(type(pattern), pattern), 2)
    end

    return get_deformat_function(pattern)(text)
end


