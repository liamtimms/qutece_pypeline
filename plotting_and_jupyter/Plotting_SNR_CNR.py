#!/usr/bin/env python
# coding: utf-8

# In[1]:

import os

import pandas as pd
import seaborn as sns

# import plotter
get_ipython().run_line_magic('matplotlib', 'inline')

# sns.set_theme(style="whitegrid", palette="muted")
sns.set_theme()

# In[2]:

full_df, filt_df = plotter.snr_compare()
full_df = full_df.loc[(full_df['noise_std'] < 1.85)]

# In[ ]:

full_df.head()

# In[ ]:

filt_df

# In[ ]:

df = filt_df.groupby(['scan_type', 'sub_num'])['SNR'].describe().round(3)
df

# In[ ]:

tof_df = filt_df.loc[(filt_df['scan_type'] == 'TOF')]
tof_df_m = tof_df.groupby(['sub_num'])['SNR'].describe().round(3)
ute_df = filt_df.loc[(filt_df['scan_type'] == 'hr')]
ute_df_m = ute_df.groupby(['sub_num'])['SNR'].describe().round(3)
ute_df_m['mean']
df = ute_df_m['mean'] / tof_df_m['mean']
df.describe().round(2)

# In[ ]:

tof_df = filt_df.loc[(filt_df['scan_type'] == 'TOF')]
tof_df_m = tof_df.groupby(['sub_num'])['ISH'].describe().round(3)
ute_df = filt_df.loc[(filt_df['scan_type'] == 'hr')]
ute_df_m = ute_df.groupby(['sub_num'])['ISH'].describe().round(3)
ute_df_m['mean']
df = tof_df_m['mean'] / ute_df_m['mean']
df.describe().round(2)

# In[ ]:

seg_type_list = ['vesselness', 'noise']

scan_type = 'hr'
hr_df_list = plotter.load_full_summary_dfs(seg_type_list, scan_type)
hr_df = pd.concat(hr_df_list, ignore_index=True)
hr_df.head()

# In[ ]:

filt_df = hr_df.loc[~hr_df['scan'].str.contains('divby')
                    & (hr_df['region'] == 1)]

y_axis = 'count'
filt_df = filt_df.reset_index()
a = filt_df['sub_num'].nunique() / 2
sns_plot = sns.catplot(
    x="sub_num",
    y=y_axis,
    hue="session",
    kind="swarm",
    row="seg_type",
    # orient="h",
    height=10,
    # aspect=2,
    data=filt_df)

# In[ ]:

m_df = hr_df.groupby(['region', 'session'])['mean'].mean()
m_df

# # All below is Tianyi's code to generate SNR CNR ISH comparison

# In[3]:

hr_csv_fname = 'FULL_SUMMARY_seg-CNR_withmotion_hr.csv'
hr_df = pd.read_csv(hr_csv_fname)
TOF_csv_fname = 'FULL_SUMMARY_seg-CNR_withmotion_TOF.csv'
TOF_df = pd.read_csv(TOF_csv_fname)
TOF_df = TOF_df.drop(columns=['index_x', 'index_y', 'index'])

cols = TOF_df.columns.tolist()
hr_df = hr_df[cols]

# In[4]:

df = pd.concat([hr_df, TOF_df])
df = df.drop(columns=['level_0'])
df.head()

# In[5]:

df.head()

# In[6]:

# This cell impose the condition: drop severe motion scans
df = df[df['severe_motion'] == 0]

# In[7]:

df_postandtof = df.loc[(df['scan_type'] == 'TOF') |
                       (df['session'] == 'Postcon')]
df_postandtof.head()

# In[8]:

SNR_stats = df_postandtof.groupby(
    ['scan_type'])['SNR'].describe()[['count', 'mean', 'std']].round(3)
SNR_stats

# In[9]:

SNR_stats_persub = df_postandtof.groupby(
    ['scan_type', 'sub_num'])['SNR'].describe()[['count', 'mean',
                                                 'std']].round(3)
#SNR_stats_persub

# In[10]:

CNR_stats = df_postandtof.groupby(
    ['scan_type'])['CNR'].describe()[['count', 'mean', 'std']].round(3)
CNR_stats

# In[13]:

CNR_stats_persub = df_postandtof.groupby(
    ['scan_type', 'sub_num'])['CNR'].describe()[['count', 'mean',
                                                 'std']].round(3)
#CNR_stats_persub

# In[11]:

ISH_stats = df_postandtof.groupby(
    ['scan_type'])['ISH'].describe()[['count', 'mean', 'std']].round(3)
ISH_stats

# In[12]:

ISH_stats_persub = df_postandtof.groupby(
    ['scan_type', 'sub_num'])['ISH'].describe()[['count', 'mean',
                                                 'std']].round(3)
#ISH_stats_persub

# In[9]:

df_postandpre = df.loc[(df['scan_type'] == 'hr')]
df_postandpre.head()

# In[10]:

posttopre_stats = df_postandpre.groupby(
    ['session', 'sub_num'])['SNR'].describe()[['count', 'mean',
                                               'std']].round(3)
posttopre_stats

# In[11]:

df_post = df.loc[(df['scan_type'] == 'hr') & (df['session'] == 'Postcon')]
df_pre = df.loc[(df['scan_type'] == 'hr') & (df['session'] == 'Precon')]
df_tof = df.loc[(df['scan_type'] == 'TOF') & (df['session'] == 'Precon')]
df_tof

# In[12]:

PostSNR = df_post.groupby(['sub_num'
                           ])['SNR'].describe()[['count', 'mean',
                                                 'std']].round(3)
PreSNR = df_pre.groupby(['sub_num'
                         ])['SNR'].describe()[['count', 'mean',
                                               'std']].round(3)
sessionCNR = PostSNR['mean'] - PreSNR['mean']
sesCNR_df = sessionCNR.describe()[['count', 'mean', 'std']].round(3)
sesCNR_df

# In[17]:

TOFSNR = df_tof.groupby(['sub_num'
                         ])['SNR'].describe()[['count', 'mean',
                                               'std']].round(3)
factor = PostSNR['mean'] / TOFSNR['mean']
factor_df = factor.describe()[['count', 'mean', 'std']].round(3)
factor_df

# In[18]:

PostISH = df_post.groupby(['sub_num'
                           ])['ISH'].describe()[['count', 'mean',
                                                 'std']].round(3)
TOFISH = df_tof.groupby(['sub_num'
                         ])['ISH'].describe()[['count', 'mean',
                                               'std']].round(3)
factor = PostISH['mean'] / TOFISH['mean']
factor_df = factor.describe()[['count', 'mean', 'std']].round(3)
factor_df

# In[19]:

PostCNR = df_post.groupby(['sub_num'
                           ])['CNR'].describe()[['count', 'mean',
                                                 'std']].round(3)
TOFCNR = df_tof.groupby(['sub_num'
                         ])['CNR'].describe()[['count', 'mean',
                                               'std']].round(3)
factor = PostCNR['mean'] / TOFCNR['mean']
factor_df = factor.describe()[['count', 'mean', 'std']].round(3)
factor_df

# ## Now plotting (Liam)

# In[13]:

filt_ute = df_postandtof.loc()

# In[39]:

subjects = set(list(df_post['sub_num'])).intersection(list(df_tof['sub_num']))

filt_df = df_postandtof
filt_df = filt_df.replace(to_replace="hr", value="QUTE-CE")
filt_df = filt_df[filt_df['sub_num'].isin(subjects)]

filt_df = filt_df.reset_index()
a = filt_df['sub_num'].nunique() / 7

filt_df.rename(columns={'sub_num': 'subject'}, inplace=True)

y_axis = 'SNR'
sns_plot = sns.catplot(x="subject",
                       y=y_axis,
                       hue="scan_type",
                       kind="bar",
                       height=7,
                       aspect=a,
                       palette=['darkorange', 'royalblue'],
                       data=filt_df)

# sns_plot.set_size_inches(11.7, 8.27)

save_name = (y_axis + '_per-subject_filtered.png')
sns_plot.savefig(save_name, dpi=300)

# In[40]:

y_axis = "ISH"
sns_plot = sns.catplot(x="subject",
                       y=y_axis,
                       hue="scan_type",
                       kind="bar",
                       height=7,
                       aspect=a,
                       palette=['darkorange', 'royalblue'],
                       data=filt_df)

save_name = (y_axis + '_per-subject_filtered.png')
sns_plot.savefig(save_name, dpi=300)

# In[24]:

filt_df.head()

# In[14]:

T1w_csv_fname = 'FULL_SUMMARY_seg-CNR_withmotion_T1w.csv'
T1w_df = pd.read_csv(T1w_csv_fname)
T1w_df = T1w_df.drop(columns=['level_0', 'index_x', 'index_y', 'index'])

cols = T1w_df.columns.tolist()
cols
#hr_df = hr_df[cols]

# In[15]:

df

# In[16]:

T1w_UTE_TOF_df = pd.concat([T1w_df, df])
# df = df.drop(columns=['level_0'])
T1w_UTE_TOF_df.tail()

# In[21]:

ISH_stats = T1w_UTE_TOF_df.groupby(
    ['scan_type', 'session'])['ISH'].describe()[['count', 'mean',
                                                 'std']].round(3)
ISH_stats

# In[22]:

stats = T1w_UTE_TOF_df.groupby(['scan_type', 'session'
                                ])['CNR'].describe()[['count', 'mean',
                                                      'std']].round(3)
stats

# In[19]:

stats = T1w_UTE_TOF_df.groupby(['scan_type', 'session', 'sub_num'
                                ])['SNR'].describe()[['count', 'mean',
                                                      'std']].round(3)
stats

# In[21]:

df_post = df.loc[(df['scan_type'] == 'hr') & (df['session'] == 'Postcon')]
df_pre = df.loc[(df['scan_type'] == 'hr') & (df['session'] == 'Precon')]
df_tof = df.loc[(df['scan_type'] == 'TOF') & (df['session'] == 'Precon')]
df_post

# In[22]:

df_T1w_post = T1w_UTE_TOF_df.loc[(T1w_UTE_TOF_df['scan_type'] == 'T1w')
                                 & (T1w_UTE_TOF_df['session'] == 'Postcon')]
df_T1w_pre = T1w_UTE_TOF_df.loc[(T1w_UTE_TOF_df['scan_type'] == 'T1w')
                                & (T1w_UTE_TOF_df['session'] == 'Precon')]
#df_tof = df.loc[(df['scan_type']=='TOF') & (df['session']=='Precon')]
df_T1w_post

# In[23]:

PostSNR_T1w = df_T1w_post.groupby(
    ['sub_num'])['SNR'].describe()[['count', 'mean', 'std']].round(3)
PreSNR_T1w = df_T1w_pre.groupby(['sub_num'
                                 ])['SNR'].describe()[['count', 'mean',
                                                       'std']].round(3)
sessionCNR_T1w = PostSNR_T1w['mean'] - PreSNR_T1w['mean']
sesCNR_df_T1w = sessionCNR_T1w.describe()[['count', 'mean', 'std']].round(3)
sesCNR_df_T1w

# In[24]:

PostSNR_T1w = df_T1w_post.groupby(
    ['sub_num'])['SNR'].describe()[['count', 'mean', 'std']].round(3)
factor = PostSNR['mean'] / PostSNR_T1w['mean']
factor_df = factor.describe()[['count', 'mean', 'std']].round(3)
factor_df

# In[25]:

df_post_withT1w = T1w_UTE_TOF_df.loc[(T1w_UTE_TOF_df['session'] == 'Postcon')]
df_post_withT1w.head()

# In[70]:

subjects = set(list(df_post['sub_num'])).intersection(
    list(df_T1w_post['sub_num']))

filt_df = df_post_withT1w
filt_df = filt_df.replace(to_replace="hr", value="QUTE-CE")
filt_df = filt_df[filt_df['sub_num'].isin(subjects)]

filt_df = filt_df.reset_index()
a = filt_df['sub_num'].nunique() / 7

filt_df.rename(columns={'sub_num': 'subject'}, inplace=True)
filt_df = filt_df.sort_values(by=['scan_type'], ascending=True)

y_axis = 'SNR'
sns_plot = sns.catplot(x="subject",
                       y=y_axis,
                       hue="scan_type",
                       kind="bar",
                       height=7,
                       aspect=a,
                       palette=['darkorange', 'seagreen'],
                       data=filt_df)

# sns_plot.set_size_inches(11.7, 8.27)

save_name = (y_axis + '_per-subject_filtered_T1w.png')
sns_plot.savefig(save_name, dpi=300)

# In[72]:

y_axis = "CNR"
sns_plot = sns.catplot(x="subject",
                       y=y_axis,
                       hue="scan_type",
                       kind="bar",
                       height=7,
                       aspect=a,
                       palette=['darkorange', 'seagreen'],
                       data=filt_df)

save_name = (y_axis + '_per-subject_filtered_T1w.png')
# save_name = (y_axis + '_per-subject_filtered.png')
sns_plot.savefig(save_name, dpi=300)

# In[50]:

filt_df = T1w_UTE_TOF_df.loc[(T1w_UTE_TOF_df['session'] == 'Postcon') |
                             (T1w_UTE_TOF_df['scan_type'] == 'TOF')]
filt_df = filt_df.replace(to_replace="hr", value="QUTE-CE")
subjects = set(list(df_post['sub_num'])).intersection(list(df_tof['sub_num']))
filt_df = filt_df[filt_df['sub_num'].isin(subjects)]

filt_df = filt_df.reset_index()
a = filt_df['sub_num'].nunique() / 5
filt_df = filt_df.sort_values(by=['scan_type'], ascending=True)

filt_df.rename(columns={'sub_num': 'subject'}, inplace=True)

y_axis = 'SNR'
sns_plot = sns.catplot(x="subject",
                       y=y_axis,
                       hue="scan_type",
                       kind="bar",
                       height=7,
                       aspect=a,
                       palette=['darkorange', 'mediumseagreen', 'slateblue'],
                       data=filt_df)

save_name = (y_axis + '_per-subject_filtered_T1w_TOF.png')
# save_name = (y_axis + '_per-subject_filtered.png')
sns_plot.savefig(save_name, dpi=300)

# In[ ]:

y_axis = 'ISH'
sns_plot = sns.catplot(x="subject",
                       y=y_axis,
                       hue="scan_type",
                       kind="bar",
                       height=7,
                       aspect=a,
                       palette=['darkorange', 'mediumseagreen', 'slateblue'],
                       data=filt_df)

# In[ ]:

# In[ ]:

# In[ ]:

# In[ ]:

# In[ ]:

# In[ ]:

# In[ ]:

# In[ ]:

# ## CBV

# In[63]:

post_ute_df = df.loc[(df['session'] == 'Postcon')]
Post = post_ute_df.groupby(['sub_num']).mean().round(3)
Post.rename(columns={
    'signal_mean': 'blood_post',
    'tissue_mean': 'tissue_post'
},
            inplace=True)
Post = Post.drop(columns=['SNR', 'CNR', 'ISH', 'severe_motion'])

pre_ute_df = df.loc[(df['session'] == 'Precon')]
Pre = pre_ute_df.groupby(['sub_num']).mean().round(3)
Pre.rename(columns={
    'signal_mean': 'blood_pre',
    'tissue_mean': 'tissue_pre'
},
           inplace=True)
Pre = Pre.drop(columns=['SNR', 'CNR', 'ISH', 'severe_motion'])

PrePost = pd.merge(Post, Pre, left_index=True, right_index=True)
PrePost['blood_diff'] = PrePost['blood_post'] - PrePost['blood_pre']
PrePost['tissue_diff'] = PrePost['tissue_post'] - PrePost['tissue_pre']
PrePost['CBV'] = PrePost['tissue_diff'] / PrePost['blood_diff']

PrePost

# In[67]:

y_axis = "CBV"
sns_plot = sns.catplot(
    x="sub_num",
    y=y_axis,
    # hue="scan_type",
    kind="bar",
    height=7,
    aspect=a,
    data=PrePost.reset_index())

save_name = (y_axis + '_per-subject_filtered.png')
sns_plot.savefig(save_name, dpi=300)

# # Phantoms

# In[6]:

csv_fname = 'QUTE-CE_T1w_Blood.csv'
phantom_df = pd.read_csv(csv_fname)
phantom_df

# In[15]:

filt_df = phantom_df.loc[~(phantom_df['Segment'] == 'Air')]
filt_df = filt_df.replace(to_replace="UTE", value="QUTE-CE")
filt_df = filt_df.replace(to_replace="CE_Blood", value="CE Blood")

filt_df = filt_df.reset_index()
# a = filt_df['sub_num'].nunique() / 5
filt_df = filt_df.sort_values(by=['scan_type'], ascending=True)

filt_df.rename(columns={'Segment': 'ROI'}, inplace=True)

y_axis = 'ISH'
sns_plot = sns.catplot(
    x="ROI",
    y=y_axis,
    hue="scan_type",
    kind="bar",
    height=7,
    #aspect=a,
    palette=['darkorange', 'mediumseagreen'],
    data=filt_df)

save_name = (y_axis + '_phantom_T1w_TOF.png')
# save_name = (y_axis + '_per-subject_filtered.png')
sns_plot.savefig(save_name, dpi=300)
