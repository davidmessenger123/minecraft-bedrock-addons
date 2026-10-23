import { world, system } from "@minecraft/server";
import { ActionFormData, ModalFormData, DropdownFormData } from "@minecraft/server-ui";

/**
 * Mobile Phone for Bedrock Edition.
 *
 * Right clicking the phone opens a small GUI that looks like a phone screen. The terminal app
 * runs commands with the permissions of the player that holds the phone, so the game itself
 * decides who may run admin commands.
 */

const ITEM_ID = "phone:mobile_phone";
const ACCENT = "§b";
const DIM = "§7";
const OK = "§a";
const BAD = "§c";

const ADMIN_ACTIONS = [
    ["Set Day", "/time set day"],
    ["Set Noon", "/time set noon"],
    ["Set Night", "/time set night"],
    ["Clear Weather", "/weather clear"],
    ["Thunderstorm", "/weather thunder"],
    ["Heal", "/effect give @s minecraft:regeneration 1 255 true"],
    ["Clear Effects", "/effect clear @s"],
    ["Creative", "/gamemode creative"],
    ["Survival", "/gamemode survival"],
    ["Give Diamond", "/give @s minecraft:diamond 1"],
    ["Kill Mobs", "/kill @e[type=!player]"],
    ["Save World", "/save-all"],
];

const SERVER_ACTIONS = [
    ["Save World", "/save-all"],
    ["List Players", "/list"],
    ["Kill Mobs", "/kill @e[type=!player]"],
    ["Remove Drops", "/kill @e[type=minecraft:item]"],
    ["Set Day", "/time set day"],
    ["Set Night", "/time set night"],
];

world.afterEvents.itemUse.subscribe((event) => {
    const stack = event.itemStack;
    if (!stack || stack.typeId !== ITEM_ID) {
        return;
    }

    const player = event.source;
    if (!player || player.typeId !== "minecraft:player") {
        return;
    }

    system.run(() => openPhone(player));
});

function openPhone(player) {
    const form = new ActionFormData()
        .title(`${ACCENT}Mobile Phone`)
        .body(phoneHeader(player))
        .button("Terminal")
        .button("Admin")
        .button("World")
        .button("Player")
        .button("Players")
        .button("Server")
        .button("Close");

    show(form, player, (selection) => {
        switch (selection.selection) {
            case 0:
                return openTerminal(player);
            case 1:
                return openAdmin(player);
            case 2:
                return openWorld(player);
            case 3:
                return openSelf(player);
            case 4:
                return openPlayers(player);
            case 5:
                return openServer(player);
            default:
                return undefined;
        }
    });
}

function openTerminal(player) {
    const form = new ModalFormData()
        .title(`${ACCENT}Terminal`)
        .body(
            `${DIM}Type a command and run it.\n` +
            `${DIM}It runs with your own permissions, so admin\n` +
            `commands only work for server operators.`
        )
        .input("Command", "/gamemode creative", "text")
        .button1("Run")
        .button2("Back");

    show(form, player, (result) => {
        if (result.canceled || result.formValue === undefined) {
            return openPhone(player);
        }

        const command = String(result.formValue).trim();
        if (!command) {
            return openTerminal(player);
        }

        runCommand(player, command);
        return openTerminal(player);
    });
}

function openAdmin(player) {
    const form = new DropdownFormData()
        .title(`${ACCENT}Admin`)
        .body(`${DIM}Pick an admin action and run it.`)
        .dropdown("Action", ADMIN_ACTIONS.map((entry) => entry[0]), 0)
        .button1("Run")
        .button2("Back");

    show(form, player, (result) => {
        if (result.canceled || result.formValue === undefined) {
            return openPhone(player);
        }

        const action = ADMIN_ACTIONS[Number(result.formValue)];
        if (action) {
            runCommand(player, action[1]);
        }
        return openAdmin(player);
    });
}

function openWorld(player) {
    const form = new ActionFormData()
        .title(`${ACCENT}World`)
        .body(
            `${DIM}World\n` +
            `${DIM}Dimension: §f${dimensionName(player)}\n` +
            `${DIM}Time: §f${clock()}\n` +
            `${DIM}Weather: §f${weather()}\n` +
            `${DIM}Players: §f${world.getAllPlayers().length}\n` +
            `${DIM}Seed: §f${seed()}\n\n` +
            `${DIM}Shortcut actions`
        )
        .button("Set Day")
        .button("Set Night")
        .button("Clear Weather")
        .button("Back");

    show(form, player, (selection) => {
        switch (selection.selection) {
            case 0:
                runCommand(player, "/time set day");
                break;
            case 1:
                runCommand(player, "/time set night");
                break;
            case 2:
                runCommand(player, "/weather clear");
                break;
            default:
                return openPhone(player);
        }
        return openWorld(player);
    });
}

function openSelf(player) {
    const health = player.getComponent("minecraft:health");
    const form = new ActionFormData()
        .title(`${ACCENT}Player`)
        .body(
            `${DIM}Operator\n` +
            `${DIM}Name: §f${player.name}\n` +
            `${DIM}Health: §f${health ? Math.round(health.currentValue) : "?"}/${health ? Math.round(health.maxValue) : "?"}\n` +
            `${DIM}Position: §f${formatPosition(player.location)}\n` +
            `${DIM}Dimension: §f${dimensionName(player)}\n\n` +
            `${DIM}Shortcut actions`
        )
        .button("Heal")
        .button("Clear Effects")
        .button("Give Diamond")
        .button("Back");

    show(form, player, (selection) => {
        switch (selection.selection) {
            case 0:
                runCommand(player, "/effect give @s minecraft:regeneration 1 255 true");
                break;
            case 1:
                runCommand(player, "/effect clear @s");
                break;
            case 2:
                runCommand(player, "/give @s minecraft:diamond 1");
                break;
            default:
                return openPhone(player);
        }
        return openSelf(player);
    });
}

function openPlayers(player) {
    const players = world.getAllPlayers();
    if (players.length === 0) {
        player.sendMessage(`${DIM}No players are online.`);
        return openPhone(player);
    }

    const form = new ActionFormData()
        .title(`${ACCENT}Players`)
        .body(`${DIM}${players.length} player(s) online. Pick one.`)
        .button(...players.map((other) => other.name))
        .button("Back");

    show(form, player, (selection) => {
        if (selection.selection < 0 || selection.selection >= players.length) {
            return openPhone(player);
        }
        return openPlayerActions(player, players[selection.selection].name);
    });
}

function openPlayerActions(player, target) {
    const form = new DropdownFormData()
        .title(`${ACCENT}${target}`)
        .body(`${DIM}Pick an action for ${target}.`)
        .dropdown(
            "Action",
            ["Heal", "Clear Effects", "Give Diamond", "Kill", "Teleport To Me"],
            0
        )
        .button1("Run")
        .button2("Back");

    show(form, player, (result) => {
        if (result.canceled || result.formValue === undefined) {
            return openPlayers(player);
        }

        const commands = [
            `/effect give ${target} minecraft:regeneration 1 255 true`,
            `/effect clear ${target}`,
            `/give ${target} minecraft:diamond 1`,
            `/kill ${target}`,
            `/tp ${target} @s`,
        ];
        runCommand(player, commands[Number(result.formValue)]);
        return openPlayerActions(player, target);
    });
}

function openServer(player) {
    const form = new DropdownFormData()
        .title(`${ACCENT}Server`)
        .body(
            `${DIM}World: §f${serverWorldName()}\n` +
            `${DIM}Players: §f${world.getAllPlayers().length}\n` +
            `${DIM}Time: §f${clock()}\n\n` +
            `${DIM}Pick a server action.`
        )
        .dropdown("Action", SERVER_ACTIONS.map((entry) => entry[0]), 0)
        .button1("Run")
        .button2("Back");

    show(form, player, (result) => {
        if (result.canceled || result.formValue === undefined) {
            return openPhone(player);
        }

        const action = SERVER_ACTIONS[Number(result.formValue)];
        if (action) {
            runCommand(player, action[1]);
        }
        return openServer(player);
    });
}

/**
 * Runs a command as the player. The game checks the permissions of the player, so only server
 * operators can actually run admin commands.
 */
function runCommand(player, command) {
    const normalized = command.startsWith("/") ? command : `/${command}`;

    let result;
    try {
        result = player.runCommand(normalized);
    } catch (error) {
        player.sendMessage(`${BAD}✖ ${normalized} could not be run`);
        return;
    }

    if (result && result.success) {
        player.sendMessage(`${OK}✔ ${normalized}`);
    } else {
        player.sendMessage(`${BAD}✖ ${normalized} failed, no permission or unknown command`);
    }
}

function show(form, player, callback) {
    form.show(player).then(callback).catch(() => {
        /* the player closed the screen */
    });
}

function phoneHeader(player) {
    return (
        `${ACCENT}Mobile Phone\n` +
        `${DIM}──────────────────\n` +
        `${DIM}Operator  §f${player.name}\n` +
        `${DIM}World     §f${serverWorldName()}\n` +
        `${DIM}Time      §f${clock()}\n` +
        `${DIM}Weather   §f${weather()}\n` +
        `${DIM}──────────────────\n` +
        `${DIM}Pick an app`
    );
}

function clock() {
    const time = world.getTimeOfDay() % 24000;
    const hours = Math.floor((time / 1000 + 6) % 24);
    const minutes = Math.floor(((time % 1000) * 60) / 1000);
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

function weather() {
    try {
        const current = world.getDimension("overworld").getWeather();
        if (current === "thunder") {
            return "Thunderstorm";
        }
        if (current === "rain") {
            return "Rain";
        }
        return "Clear";
    } catch (error) {
        return "Unknown";
    }
}

function dimensionName(player) {
    try {
        return player.dimension.id.replace("minecraft:", "");
    } catch (error) {
        return "unknown";
    }
}

function serverWorldName() {
    try {
        return world.getDimension("overworld").id.replace("minecraft:", "");
    } catch (error) {
        return "world";
    }
}

function seed() {
    try {
        return String(world.getDynamicProperty("phone:seed") ?? "hidden");
    } catch (error) {
        return "hidden";
    }
}

function formatPosition(location) {
    if (!location) {
        return "?";
    }
    return `${Math.round(location.x)}, ${Math.round(location.y)}, ${Math.round(location.z)}`;
}
