from mido import Message, MidiFile, MidiTrack, MetaMessage
import json

def bpm2tempo(bpm):
    return int(60000000/bpm)

#assign file, key and scale
mid = MidiFile('midi_in.mid', clip=True)

key = 'E'
degrees = ''
scale = 'Aeolian'

# load midi notes that grabs midi number values with note as key
with open('midinotes.json') as json_file:
    midi_notes = json.load(json_file)

#print(midi_notes) 

# load music scales
with open('all_music_scales.json') as f:
    music_scales = json.load(f)

# load chords
with open('all_chords.json') as f:
    all_chords = json.load(f)

# load midi_to_notes dictionary that grabs note values with midi number as key
with open('midi_to_notes.json') as f:
    midi_to_notes = json.load(f)

# function to collect notes from a midi file from their channels return a list of notes per track
mid = MidiFile('midi_in.mid', clip=True)

# function to collect notes. must collect all notes note_on and note_off so they can all be adjusted
def collect_notes(mid):
    tracks = []
    note_collection = []
    for i, track in enumerate(mid.tracks):
        for msg in track:
            if 'note_' in str(msg) and 'note=' in str(msg):
                note_collection.append(midi_to_notes[str(msg.note)])
                #print('*******')
        if note_collection:
            tracks.append(note_collection)
            note_collection = []
    return tracks

# run collect notes function
notes_array = collect_notes(mid)

# take collection of notes and strip the numbers
track_note_set = []
only_note_set = set()
only_note_list = []
for track in notes_array:
    for notes in track:
        only_note_list.append(''.join(i for i in notes if not i.isdigit()))
    track_note_set.append(only_note_list)
    only_note_list = []


# get the scale using above identifiers
selected_scale = [i for i in music_scales if scale in i['name']][0][key]
# degrees from a selected music scale
degrees = [i for i in music_scales if scale in i['name']][0]['degrees'].split(' ')
# selected scale to degrees
sel_sc_deg = dict()
# selected degress to scale (not needed yet)
sel_deg_sc = dict()

selected_scale_dict = dict(zip(degrees, selected_scale))

for a, b in selected_scale_dict.items():
    sel_sc_deg[b] = a

sel_deg_sc = {j:i for i, j in sel_sc_deg.items()}

deg_sc = []
sc_deg = []
name = []

for i in music_scales:
    name.append(i['name'])
    deg_sc.append(dict(zip(i['degrees'].split(' '), i[key])))
    sc_deg.append(dict(zip(i[key], i['degrees'].split(' '))))

print()
named_sc_deg = dict(zip(name,sc_deg))
named_deg_sc = dict(zip(name, deg_sc))

# function to check if note is a sharp/flat
def has_sharp(note):
    if '#' in note:
        return True
    else:
        return False

# function to strip numbers for multiple uses in this code
def strip_numbers(mylist):
    return [''.join(char for char in s if not char.isdigit()) for s in mylist]

def strip_non_num(mylist):
    return [''.join(char for char in s if char.isdigit()) for s in mylist]

# get the list of notes not in the scale
notes_used = list(set(strip_numbers(notes_array[0])))

# scan for notes not used in the selected scale and assign to a list
def non_scale_notes(my_played, scale_used):
    return_list = []
    for i in my_played:
        if i not in scale_used:
            return_list.append(i)
    return return_list

#print(non_scale_notes(notes_used, selected_scale ))
error_notes = non_scale_notes(notes_used, selected_scale)

# get the degree pattern used in the orignal midi file
deg_pat = []
note_oct = [''.join(char for char in string if char.isdigit()) for string in notes_array[0]]

stripped_midi_notes = strip_numbers(notes_array[0])

for midnote in stripped_midi_notes:
    try:
        deg_pat.append(sel_sc_deg[midnote])
    except:
        deg_pat.append('error')

stripped_deg_pat = strip_non_num(deg_pat)

# check if deg_sc 7 note scales have the numbers 1-7
degrees = []
for i in range(1,len(sel_deg_sc)+1):
    degrees.append(str(i))

# collect scales that dont have the necessary degrees

named_scale_set = named_deg_sc.copy()
named_removed= dict()
for name, scale in named_scale_set.items():
    #print(scale)
    for i in degrees:
    #    print(name)
    #    print(i, list(scale.keys()))
        if i not in str(list(scale.keys())):
            named_removed[name] = named_scale_set[name]
            break

# remove scales that don't have the necessary degrees

for i in named_removed:
    try:
        del named_scale_set[i]
    except:
        pass
        #print('dne/already deleted')
  # get rid of chromatic scale
try:
    del  named_scale_set['Chromatic']
except:
    pass
    #print('dne')

# get the list of degrees that the notes played translated to for each of the scales
named_new_mid_deg = dict()
temp_mid_list = []
for name, scale in named_scale_set.items():
    for i in stripped_deg_pat:
        for j in list(scale.keys()):
            if i == '':
                temp_mid_list.append('error')
                break
            if i in j:
                temp_mid_list.append(j)
                break
    named_new_mid_deg[name] = (temp_mid_list)
    temp_mid_list = []

named_new_mid_notes = dict()
named_new_midi_compile = dict()
temp_midi_list = []
for name, scale, in named_new_mid_deg.items():
    #print(name, scale)
    for n, i in enumerate(named_new_mid_deg[name]):
        try:
#            print(n, i)
#            print(named_scale_set[name][i])
#            print()
            temp_midi_list.append(midi_notes[named_scale_set[name][i]+note_oct[n]])
        except:
            temp_midi_list.append('error')
    named_new_midi_compile[name] = temp_midi_list
    temp_midi_list = []

# remove scales that are repeats
all_notes_played = dict()
temp_list = []
for name, scale in named_new_midi_compile.items():
    for i in list(set(scale)):
        if type(i) == int:
            temp_list.append(i)
    temp_list.sort()
    all_notes_played[name] = temp_list
    temp_list = []

# select the scales you want to removed
remove_scales = ['Melodic minor(descending)', 'Bebop dominant', 'Chromatic', 'Double harmonic', 'Bebop major']
for name in remove_scales:
    try:
        del named_new_midi_compile[name]
    except:
        pass

# replace notes with new scale notes

new_midi_msgs = []
note_msgs = []
# filter for, and store midi header msgs
midi_header_msgs = []
for i, track in enumerate(mid.tracks):
    for n, msg in enumerate(track):
        if 'note_' in str(msg) and 'note=' in str(msg):
            note_msgs.append(msg)
        else:
            midi_header_msgs.append(msg)

midi_end_msg = midi_header_msgs.pop()

named_new_note_msgs = dict()
temp_list = []
for name, scale in named_new_midi_compile.items():
    for n, i in enumerate(note_msgs):
        if isinstance(scale[n], int):
            #named_new_note_msgs[name].append(i.copy(note=))
            #print(n, ',', named_new_midi_compile[name][n])
            temp_list.append(i.copy(note=named_new_midi_compile[name][n]))
        else:
            #print(named_new_midi_compile[name][n])
            temp_list.append(i.copy(velocity=0))
    named_new_note_msgs[name] = temp_list
    temp_list = []

# write msgs to miditracks and create files
newMid = dict()
testTrack = dict()
for name, msgs in named_new_note_msgs.items():
    newMid[name] = MidiFile()
    newMid[name].ticks_per_beat = 96
    testTrack[name] = MidiTrack()

for name, msg in testTrack.items():
    for i in midi_header_msgs:
        testTrack[name].append(i)
    for j in named_new_note_msgs[name]:
        testTrack[name].append(j)
    testTrack[name].append(midi_end_msg)

for name, track in newMid.items():
    newMid[name].tracks.append(testTrack[name])
    newMid[name].tracks[0].name = name
    newMid[name].save('midibatch/'+name+'.mid')

