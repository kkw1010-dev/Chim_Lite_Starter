// Generates "CHIM Lite - Dialogue Chat.esp": one NPC dialogue option that opens
// CHIM's text entry (making the NPC a temporary agent first), and one option on
// temporary agents that releases them. The dialogue shape follows a generator
// the author wrote earlier for another mod, which was verified in game.
//
// Usage: dotnet run -c Release -- <output.esp>
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Binary.Parameters;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Strings;
using Mutagen.Bethesda.Strings.DI;
using Mutagen.Bethesda.Plugins.Binary.Streams;
using Noggog;

var output = args.Length > 0 ? args[0] : "CHIM Lite - Dialogue Chat.esp";
var modKey = ModKey.FromFileName(Path.GetFileName(output));
var mod = new SkyrimMod(modKey, SkyrimRelease.SkyrimSE);
mod.ModHeader.Flags |= SkyrimModHeader.HeaderFlag.Small; // ESL-flagged .esp

FormKey Id(uint id) => new(modKey, id);
FormKey Vanilla(uint id) => new(new ModKey("Skyrim", ModType.Master), id);
FormKey Chim(uint id) => new(new ModKey("AIAgent", ModType.Plugin), id);

// Read out of the load order with houseCARL on 2026-09-25, not recalled.
var chimControlQuest = Chim(0x0093FC); // AIAgentPapyrusFunctions quest: AIAgentFunctions + AIAgentPapyrusFunctions
var playerRef = Vanilla(0x000014);
var actorTypeNpc = Vanilla(0x013794);  // ActorTypeNPC keyword
// DialogueGenericSharedInfo lines, voiced for all 42 generic humanoid voice types
// (counted in Skyrim - Voices_en0.bsa on 2026-09-25); no conditions of their own.
var ofCourse = Vanilla(0x0DBA22);    // "Of course."
var understand = Vanilla(0x0DBA21);  // "I understand."

// Light-plugin ids live in 0x800..0xFFF.
const uint IdQuest = 0x800, IdFaction = 0x801;
const uint IdTalkTopic = 0x810, IdTalkBranch = 0x811, IdTalkInfo = 0x812;
const uint IdEndTopic = 0x820, IdEndBranch = 0x821, IdEndInfo = 0x822;

var tempFaction = new Faction(Id(IdFaction), SkyrimRelease.SkyrimSE)
{
    EditorID = "TKLChimChatTempAgentFaction",
    Name = "CHIM temporary agent",
};
mod.Factions.Add(tempFaction);

var quest = new Quest(Id(IdQuest), SkyrimRelease.SkyrimSE)
{
    EditorID = "TKLChimChatQuest",
    Name = "CHIM Dialogue Chat",
    Priority = 50,
    Type = Quest.TypeEnum.None,
};
// 0x011: StartGameEnabled plus the unnamed bit every vanilla dialogue quest carries
// (vanilla DialogueGeneric and DialogueWhiterun carry it).
quest.Flags |= Quest.Flag.StartGameEnabled;
quest.Flags |= (Quest.Flag)0x010;
mod.Quests.Add(quest);

ScriptObjectProperty Obj(string name, FormKey target, short alias = -1) => new()
{
    Name = name,
    Object = target.ToLink<ISkyrimMajorRecordGetter>(),
    Alias = alias,
};

var controller = new ScriptEntry { Name = "TKLChimChatController", Flags = ScriptEntry.Flag.Local };
controller.Properties.Add(Obj("ChimControl", chimControlQuest));
controller.Properties.Add(Obj("TempAgentFaction", tempFaction.FormKey));
controller.Properties.Add(Obj("PlayerRef", playerRef));

// Alias 0 holds the player, for OnPlayerLoadGame and OnLocationChange.
// Flags and VoiceTypes are written explicitly (0 and a null link) because every
// CK-authored reference alias carries FNAM and VTCK; houseCARL's parity check flags
// an alias without them.
var playerAlias = new QuestAlias { ID = 0, Name = "Player", Flags = 0 };
playerAlias.ForcedReference.SetTo(playerRef);
playerAlias.VoiceTypes.SetTo(FormKey.Null);
quest.Aliases.Add(playerAlias);
quest.NextAliasID = 1;

var aliasScript = new ScriptEntry { Name = "TKLChimChatPlayerAlias", Flags = ScriptEntry.Flag.Local };
aliasScript.Properties.Add(Obj("Controller", quest.FormKey));
var adapter = new QuestAdapter { Version = 5, ObjectFormat = 2 };
adapter.Scripts.Add(controller);
adapter.Aliases.Add(new QuestFragmentAlias
{
    Property = new ScriptObjectProperty { Object = quest.ToLink<ISkyrimMajorRecordGetter>(), Alias = 0 },
    Version = 5,
    ObjectFormat = 2,
    Scripts = new ExtendedList<ScriptEntry> { aliasScript },
});
quest.VirtualMachineAdapter = adapter;

void AddTopic(string id, uint topicId, uint branchId, uint infoId, string prompt, FormKey sharedInfo,
              string fragment, IEnumerable<Condition> conditions)
{
    var topic = new DialogTopic(Id(topicId), SkyrimRelease.SkyrimSE)
    {
        EditorID = id + "Topic",
        Name = prompt,
        Priority = 50f,
        Category = DialogTopic.CategoryEnum.Topic,
        Subtype = DialogTopic.SubtypeEnum.Custom,
        SubtypeName = new RecordType("CUST"),
    };
    topic.Quest.SetTo(quest);
    mod.DialogTopics.Add(topic);

    // A player topic outside a top-level branch is never offered.
    var branch = new DialogBranch(Id(branchId), SkyrimRelease.SkyrimSE)
    {
        EditorID = id + "Branch",
        Flags = DialogBranch.Flag.TopLevel,
        Category = DialogBranch.CategoryType.Player,
    };
    branch.Quest.SetTo(quest);
    branch.StartingTopic.SetTo(topic);
    topic.Branch.SetTo(branch);
    mod.DialogBranches.Add(branch);

    var info = new DialogResponses(Id(infoId), SkyrimRelease.SkyrimSE)
    {
        EditorID = id + "Info",
        Prompt = prompt,
        Flags = new DialogResponseFlags { Flags = DialogResponses.Flag.Goodbye },
        // CNAM: every CK-authored INFO has it; without it the CK crashes opening the topic.
        FavorLevel = FavorLevel.None,
    };
    // Shared Info (DNAM): the NPC speaks a vanilla generic line, in its own voice type,
    // with the vanilla (localized) subtitle. Voice files stay in the game's own BSA;
    // nothing is copied into this mod. The INFO carries no responses of its own.
    info.ResponseData.SetTo(sharedInfo);
    info.Conditions.AddRange(conditions);

    var entry = new ScriptEntry { Name = fragment, Flags = ScriptEntry.Flag.Local };
    entry.Properties.Add(Obj("TKLChimChatQuest", quest.FormKey));
    var infoAdapter = new DialogResponsesAdapter
    {
        Version = 5,
        ObjectFormat = 2,
        ScriptFragments = new ScriptFragments
        {
            FileName = fragment,
            // End fragment: the action follows the NPC's short line, as the menu closes.
            OnEnd = new ScriptFragment { ScriptName = fragment, FragmentName = "Fragment_0" },
        },
    };
    infoAdapter.Scripts.Add(entry);
    info.VirtualMachineAdapter = infoAdapter;
    topic.Responses.Add(info);
}

Condition HasKeyword(FormKey keyword)
{
    var data = new HasKeywordConditionData();
    data.Keyword.Link.SetTo(keyword);
    return new ConditionFloat { CompareOperator = CompareOperator.EqualTo, ComparisonValue = 1f, Data = data };
}

Condition InFaction(FormKey faction)
{
    var data = new GetInFactionConditionData();
    data.Faction.Link.SetTo(faction);
    return new ConditionFloat { CompareOperator = CompareOperator.EqualTo, ComparisonValue = 1f, Data = data };
}

AddTopic("TKLChimChatTalk", IdTalkTopic, IdTalkBranch, IdTalkInfo,
         "[AI] 이야기 좀 하자.", ofCourse,
         "TKLChimChatTalkFragment", new[] { HasKeyword(actorTypeNpc) });

AddTopic("TKLChimChatEnd", IdEndTopic, IdEndBranch, IdEndInfo,
         "[AI] 이야기는 여기까지 하지.", understand,
         "TKLChimChatEndFragment", new[] { InFaction(tempFaction.FormKey) });

// Korean text must be UTF-8: Mutagen's default Windows-1252 turns Hangul into '?'.
mod.WriteToBinary(output, new BinaryWriteParameters
{
    Encodings = new EncodingBundle(MutagenEncoding._utf8, MutagenEncoding._utf8),
});

// ---- SEQ ---------------------------------------------------------------------------
// A plugin whose start-game-enabled quest owns dialogue needs SEQ\<plugin>.seq, or the
// quest stays dormant on a fresh game and the topics never show (found in an earlier mod:
// the steward topic was missing from every new game). One uint32 per start-game-enabled
// quest the plugin defines; the top byte is the plugin's own index after its masters.
var seqDir = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(output))!, "SEQ");
Directory.CreateDirectory(seqDir);
var seqPath = Path.Combine(seqDir, modKey.Name + ".seq");
// Written below, once the master list exists: Mutagen fills it in at write time.

// ---- Verify by reading the file back; any mismatch fails the build ----------------
using var check = SkyrimMod.CreateFromBinaryOverlay(output, SkyrimRelease.SkyrimSE,
    new Mutagen.Bethesda.Plugins.Binary.Parameters.BinaryReadParameters
    {
        StringsParam = new StringsReadParameters { NonLocalizedEncodingOverride = MutagenEncoding._utf8 }
    });
var failures = new List<string>();
void Expect(bool ok, string what) { if (!ok) failures.Add(what); }

var masters = check.ModHeader.MasterReferences.Select(m => m.Master.FileName.String).ToList();
Expect(masters.SequenceEqual(new[] { "Skyrim.esm", "AIAgent.esp" }), $"masters are {string.Join(", ", masters)}");
Expect(check.ModHeader.Flags.HasFlag(SkyrimModHeader.HeaderFlag.Small), "ESL flag missing");
Expect(check.Quests.Count == 1 && check.Quests.First().Flags.HasFlag(Quest.Flag.StartGameEnabled), "quest missing or not start-game-enabled");
var q = check.Quests.First();
Expect(q.VirtualMachineAdapter?.Scripts.Any(s => s.Name == "TKLChimChatController") == true, "controller script not attached");
Expect(q.VirtualMachineAdapter?.Aliases.SelectMany(a => a.Scripts).Any(s => s.Name == "TKLChimChatPlayerAlias") == true, "player alias script not attached");
Expect(check.DialogBranches.Count == 2 && check.DialogBranches.All(b => b.Flags is { } f && f.HasFlag(DialogBranch.Flag.TopLevel)), "branches not top-level");
foreach (var t in check.DialogTopics)
{
    var r = t.Responses.Single();
    Expect(r.Prompt?.String?.Contains("[AI]") == true && !r.Prompt.String.Contains('?'), $"{t.EditorID}: prompt not stored as Korean UTF-8: {r.Prompt?.String}");
    Expect(r.Flags?.Flags.HasFlag(DialogResponses.Flag.Goodbye) == true, $"{t.EditorID}: not a goodbye line");
    Expect(r.VirtualMachineAdapter?.ScriptFragments?.OnEnd?.ScriptName is { } n && n.EndsWith("Fragment"), $"{t.EditorID}: end fragment missing");
    Expect(r.Conditions.Count == 1, $"{t.EditorID}: expected one condition, found {r.Conditions.Count}");
    Expect(r.Responses.Count == 0 && r.ResponseData.FormKeyNullable is { } shared && shared.ModKey.FileName == "Skyrim.esm",
           $"{t.EditorID}: expected a Skyrim.esm shared info and no own responses");
    Console.WriteLine($"  {t.EditorID}: \"{r.Prompt?.String}\" -> shared info {r.ResponseData.FormKeyNullable}");
}
uint fileIndex = (uint)masters.Count;
var seqBytes = check.Quests.Where(x => x.Flags.HasFlag(Quest.Flag.StartGameEnabled))
    .OrderBy(x => x.FormKey.ID)
    .SelectMany(x => BitConverter.GetBytes((fileIndex << 24) | x.FormKey.ID)).ToArray();
File.WriteAllBytes(seqPath, seqBytes);
var seqBack = File.ReadAllBytes(seqPath);
Expect(seqBack.Length == 4 && BitConverter.ToUInt32(seqBack, 0) == ((uint)masters.Count << 24 | IdQuest),
       $"SEQ does not list the quest as {(uint)masters.Count << 24 | IdQuest:X8}");
foreach (var r in check.DialogTopics.SelectMany(t => t.Responses))
    Expect(r.FavorLevel == FavorLevel.None, $"{r.EditorID}: FavorLevel (CNAM) not written");
Expect(q.Aliases.Single().Flags is not null, "player alias FNAM not written");
if (failures.Count > 0)
{
    foreach (var f in failures) Console.Error.WriteLine("FAIL " + f);
    return 1;
}
Console.WriteLine($"  SEQ {BitConverter.ToUInt32(seqBack, 0):X8} -> {seqPath}");
Console.WriteLine($"OK {output}: masters {string.Join(", ", masters)}; ESL; 1 quest, 1 faction, 2 topics");
return 0;
