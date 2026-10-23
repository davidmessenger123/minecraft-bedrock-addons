import { world, system } from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";

/**
 * Mobile Phone for Bedrock Edition.
 *
 * Right-click the phone to open a form-based phone UI. Commands are run with
 * `player.runCommand`, so the game's own permission system decides who may use
 * the admin shortcuts. The script only uses @minecraft/server-ui 2.0.0 APIs:
 * ActionFormData, ModalFormData and formValues.
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
    ["Heal", "/effect give @s regeneration 1 255 true"],
    ["Clear Effects", "/effect clear @s"],
    ["Creative", "/gamemode creative"],
    ["Survival", "/gamemode survival"],
    ["Give Diamond", "/give @s diamond 1"],
    ["Kill Mobs", "/kill @e[type=!player]"],
    ["Set Spawn", "/spawnpoint @s"],
];

const SERVER_ACTIONS = [
    ["Set Day", "/time set day"],
    ["Set Night", "/time set night"],
    ["Clear Weather", "/weather clear"],
    ["Thunderstorm", "/weather thunder"],
    ["List Players", "/list"],
    ["Kill Mobs", "/kill @e[type=!player]"],
    ["Remove Drops", "/kill @e[type=item]"],
    ["Set World Spawn", "/setworldspawn"],
];

const PLAYER_ACTIONS = [
    ["Heal", (target) => `/effect give ${target} minecraft:regeneration 1 255 true`],
    ["Clear Effects", (target) => `/effect clear ${target}`],
    ["Give Diamond", (target) => `/give ${target} minecraft:diamond 1`],
    ["Kill", (target) => `/kill ${target}`],
    ["Teleport To Me", (target) => `/tp ${target} @s`],
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

    // Defer by one tick so the use animation finishes before the form opens.
    system.run(() => {
        openPhone(player).catch(() => {
            /* The player may have disconnected while the form was open. */
        });
    });
});

async function openPhone(player) {
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

    const response = await showForm(form, player);
    if (!response || response.canceled) {
        return;
    }

    switch (response.selection) {
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
}

async function openTerminal(player) {
    const form = new ModalFormData()
        .title(`${ACCENT}Terminal`)
        .label(`${DIM}Type a command and run it.`)
        .label(`${DIM}It runs with your own permissions, so admin`)
        .label(`${DIM}commands only work for server operators.`)
        .textField("Command", "/time set day", { defaultValue: "/time set day" })
        .submitButton("Run");

    const response = await showForm(form, player);
    if (!response || response.canceled) {
        return openPhone(player);
    }

    const value = firstFormValue(response, "");
    const command = typeof value === "string" ? value.trim() : "";
    if (command) {
        runCommand(player, command);
    }
    return openTerminal(player);
}

async function openAdmin(player) {
    const form = new ModalFormData()
        .title(`${ACCENT}Admin`)
        .label(`${DIM}Pick an admin action and run it.`)
        .dropdown("Action", ADMIN_ACTIONS.map((entry) => entry[0]), {
            defaultValueIndex: 0,
        })
        .submitButton("Run");

    const response = await showForm(form, player);
    if (!response || response.canceled) {
        return openPhone(player);
    }

    const index = Number(firstFormValue(response, 0));
    const action = ADMIN_ACTIONS[index];
    if (action) {
        runCommand(player, action[1]);
    }
    return openAdmin(player);
}

async function openWorld(player) {
    const form = new ActionFormData()
        .title(`${ACCENT}World`)
        .body(
            `${DIM}World\n` +
            `${DIM}Dimension  §f${dimensionName(player)}\n` +
            `${DIM}Day        §f${day()}\n` +
            `${DIM}Time       §f${clock()}\n` +
            `${DIM}Players    §f${world.getAllPlayers().length}\n\n` +
            `${DIM}Shortcut actions`
        )
        .button("Set Day")
        .button("Set Night")
        .button("Clear Weather")
        .button("Set Spawn")
        .button("Back");

    const response = await showForm(form, player);
    if (!response || response.canceled) {
        return openPhone(player);
    }

    switch (response.selection) {
        case 0:
            runCommand(player, "/time set day");
            break;
        case 1:
            runCommand(player, "/time set night");
            break;
        case 2:
            runCommand(player, "/weather clear");
            break;
        case 3:
            runCommand(player, "/spawnpoint @s");
            break;
        default:
            return openPhone(player);
    }
    return openWorld(player);
}

async function openSelf(player) {
    const form = new ActionFormData()
        .title(`${ACCENT}Player`)
        .body(
            `${DIM}Name       §f${player.name}\n` +
            `${DIM}Health     §f${healthText(player)}\n` +
            `${DIM}Position   §f${formatPosition(player.location)}\n` +
            `${DIM}Dimension  §f${dimensionName(player)}\n\n` +
            `${DIM}Shortcut actions`
        )
        .button("Heal")
        .button("Clear Effects")
        .button("Give Diamond")
        .button("Back");

    const response = await showForm(form, player);
    if (!response || response.canceled) {
        return openPhone(player);
    }

    switch (response.selection) {
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
}

async function openPlayers(player) {
    const players = world.getAllPlayers();
    const form = new ActionFormData()
        .title(`${ACCENT}Players`)
        .body(`${DIM}${players.length} player(s) online. Pick one.`);

    for (const other of players) {
        form.button(other.name);
    }
    form.button("Back");

    const response = await showForm(form, player);
    if (!response || response.canceled) {
        return openPhone(player);
    }

    if (response.selection < 0 || response.selection >= players.length) {
        return openPhone(player);
    }
    return openPlayerActions(player, players[response.selection].name);
}

async function openPlayerActions(player, target) {
    const form = new ModalFormData()
        .title(`${ACCENT}${target}`)
        .label(`${DIM}Pick an action for ${target}.`)
        .dropdown("Action", PLAYER_ACTIONS.map((entry) => entry[0]), {
            defaultValueIndex: 0,
        })
        .submitButton("Run");

    const response = await showForm(form, player);
    if (!response || response.canceled) {
        return openPlayers(player);
    }

    const index = Number(firstFormValue(response, 0));
    const action = PLAYER_ACTIONS[index];
    if (action) {
        runCommand(player, action[1](target));
    }
    return openPlayerActions(player, target);
}

async function openServer(player) {
    const form = new ModalFormData()
        .title(`${ACCENT}Server`)
        .label(`${DIM}World: §f${dimensionName(player)}`)
        .label(`${DIM}Day: §f${day()}`)
        .label(`${DIM}Players: §f${world.getAllPlayers().length}`)
        .dropdown("Action", SERVER_ACTIONS.map((entry) => entry[0]), {
            defaultValueIndex: 0,
        })
        .submitButton("Run");

    const response = await showForm(form, player);
    if (!response || response.canceled) {
        return openPhone(player);
    }

    const index = Number(firstFormValue(response, 0));
    const action = SERVER_ACTIONS[index];
    if (action) {
        runCommand(player, action[1]);
    }
    return openServer(player);
}

async function showForm(form, player) {
    try {
        return await form.show(player);
    } catch (error) {
        try {
            player.sendMessage(`${BAD}Close any open menu and try again.`);
        } catch (ignored) {
            /* The player may have disconnected. */
        }
        return undefined;
    }
}

/**
 * Returns the first defined value from a modal form response.
 *
 * In @minecraft/server-ui 2.0.0 labels, headers and dividers occupy slots in
 * `formValues` as `undefined`, so a form's first input is not necessarily at
 * index 0. Every phone form has a single input, so the first defined value is
 * the one we want. This also works on builds that omit non-input slots.
 */
function firstFormValue(response, fallback) {
    const values = response?.formValues;
    if (!Array.isArray(values)) {
        return fallback;
    }
    for (const value of values) {
        if (value !== undefined) {
            return value;
        }
    }
    return fallback;
}

/**
 * Runs a command as the player. Bedrock checks the player's permissions, so
 * only server operators can actually run the admin shortcuts.
 */
function runCommand(player, command) {
    const normalized = command.startsWith("/") ? command : `/${command}`;

    try {
        const result = player.runCommand(normalized);
        if (result && result.successCount > 0) {
            player.sendMessage(`${OK}✔ ${normalized}`);
        } else {
            player.sendMessage(`${BAD}✖ ${normalized} failed`);
        }
    } catch (error) {
        player.sendMessage(`${BAD}✖ ${normalized} could not run (permission or syntax)`);
    }
}

function phoneHeader(player) {
    return (
        `${DIM}Operator   §f${player.name}\n` +
        `${DIM}World      §f${dimensionName(player)}\n` +
        `${DIM}Day        §f${day()}\n` +
        `${DIM}Time       §f${clock()}\n` +
        `${DIM}Players    §f${world.getAllPlayers().length}\n` +
        `${DIM}──────────────────\n` +
        `${DIM}Pick an app`
    );
}

function clock() {
    try {
        const time = world.getTimeOfDay() % 24000;
        const hours = Math.floor((time / 1000 + 6) % 24);
        const minutes = Math.floor(((time % 1000) * 60) / 1000);
        return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
    } catch (error) {
        return "?";
    }
}

function day() {
    try {
        return String(world.getDay());
    } catch (error) {
        return "?";
    }
}

function dimensionName(player) {
    try {
        return player.dimension.id.replace("minecraft:", "");
    } catch (error) {
        return "unknown";
    }
}

function healthText(player) {
    try {
        const health = player.getComponent("minecraft:health");
        if (!health) {
            return "?";
        }
        return `${Math.round(health.currentValue)}/${Math.round(health.effectiveMax)}`;
    } catch (error) {
        return "?";
    }
}

function formatPosition(location) {
    if (!location) {
        return "?";
    }
    return `${Math.round(location.x)}, ${Math.round(location.y)}, ${Math.round(location.z)}`;
}
