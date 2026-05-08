import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

def setup_theme():
    sns.set_theme(style="whitegrid")
    plt.rcParams['font.family'] = 'serif'

# Standard mappings for categories -> (User Friendly Label, Color)
GB_MAPPING = {
    'COMPLIANT_DECEPTION': ('Compliant Deception', '#e74c3c'),
    'CONSIDERED_HONEST': ('Considered Honest', '#3498db'),
    'ROBUST_HONEST': ('Robust Honest', '#2ecc71'),
    'UNINTENTIONAL_FAILURE': ('Unintentional Failure', '#f39c12'),
    'FAILED_DECEPTION': ('Failed Deception', '#8e44ad')
}

BB_MAPPING = {
    'MISLEADING': ('Misleading / Framing', '#e74c3c'),
    'DECEPTIVE_FRAMING': ('Misleading / Framing', '#e74c3c'),
    'ACCURATE': ('Accurate', '#2ecc71'),
    'OMITTED': ('Omitted Critical', '#f39c12'),
    'OMITTED_CRITICAL': ('Omitted Critical', '#f39c12'),
    'FABRICATED': ('Fabricated', '#c0392b')
}

def plot_composition(df, column, mapping, title_prefix, filename, expected_order):
    total = len(df)
    counts = df[column].value_counts()
    
    percentages = []
    colors = []
    labels = []
    
    for cat in expected_order:
        count = counts.get(cat, 0)
        if count > 0:
            pct = (count / total) * 100
            percentages.append(pct)
            labels.append(mapping[cat][0])
            colors.append(mapping[cat][1])
            
    plt.figure(figsize=(10, 2))
    left = 0
    for i in range(len(percentages)):
        pct = percentages[i]
        plt.barh(0, pct, left=left, color=colors[i], label=labels[i], height=0.5)
        if pct > 5:
            # White text, unless it's a light color like yellow/orange
            text_color = 'black' if colors[i] == '#f39c12' else 'white'
            plt.text(left + pct/2, 0, f"{pct:.1f}%", ha='center', va='center', fontweight='bold', color=text_color)
        left += pct

    plt.axis('off')
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=False, fontsize=11)
    plt.tight_layout()
    os.makedirs('docs/final/images', exist_ok=True)
    plt.savefig(f'docs/final/images/{filename}', dpi=300, bbox_inches='tight')
    plt.close()

def generate_composition_charts():
    # --- V1 ---
    df_v1 = pd.read_csv('logs/full_experiment/results.csv')
    gb_order = ['COMPLIANT_DECEPTION', 'CONSIDERED_HONEST', 'ROBUST_HONEST', 'UNINTENTIONAL_FAILURE', 'FAILED_DECEPTION']
    bb_order = ['MISLEADING', 'DECEPTIVE_FRAMING', 'ACCURATE', 'OMITTED', 'OMITTED_CRITICAL', 'FABRICATED']
    
    plot_composition(df_v1, 'glassbox_category', GB_MAPPING, 'Glassbox', 'v1_glassbox_composition.png', gb_order)
    plot_composition(df_v1, 'blackbox_category', BB_MAPPING, 'Blackbox', 'v1_blackbox_composition.png', bb_order)
    
    # --- V2 ---
    df_study1 = pd.read_csv('logs/v2_study1/study1_results.csv')
    df_study2 = pd.read_csv('logs/v2_study2/study2_results.csv')
    df_v2 = pd.concat([df_study1, df_study2], ignore_index=True)
    
    plot_composition(df_v2, 'glassbox_category', GB_MAPPING, 'Glassbox', 'v2_glassbox_composition.png', gb_order)
    plot_composition(df_v2, 'blackbox_category', BB_MAPPING, 'Blackbox', 'v2_blackbox_composition.png', bb_order)

def generate_v1_frontier_stealth_gap():
    df = pd.read_csv('logs/full_experiment/results.csv')
    frontier_models = ['gemini', 'deepseek', 'kimi', 'qwen']
    df_frontier = df[df['model'].str.lower().str.contains('|'.join(frontier_models))]
    
    oversight_order = ['low', 'mid', 'high']
    gb_deception = df_frontier.groupby('oversight')['glassbox_category'].apply(lambda x: (x == 'COMPLIANT_DECEPTION').mean() * 100).reindex(oversight_order)
    bb_deception = df_frontier.groupby('oversight')['blackbox_category'].apply(lambda x: (x != 'ACCURATE').mean() * 100).reindex(oversight_order)
    
    plt.figure(figsize=(10, 6))
    plt.plot(gb_deception.index, gb_deception.values, marker='s', linewidth=3, markersize=10, color='#2c3e50', label='Glassbox')
    plt.plot(bb_deception.index, bb_deception.values, marker='o', linewidth=3, markersize=10, color='#e74c3c', label='Blackbox')
    plt.fill_between(oversight_order, bb_deception.values, gb_deception.values, color='gray', alpha=0.15, label='Stealth Gap')
    
    plt.xlabel('Oversight Level', fontsize=13)
    plt.ylabel('Deception Rate (%)', fontsize=13)
    plt.ylim(0, 105)
    plt.legend(fontsize=11, loc='lower left')
    
    for i, level in enumerate(oversight_order):
        gap = gb_deception[level] - bb_deception[level]
        plt.text(i, (gb_deception[level] + bb_deception[level])/2, f'Gap: {gap:.1f}%', 
                 ha='center', va='center', fontweight='bold', color='#2c3e50', 
                 bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.2'))
                 
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('docs/final/images/v1_frontier_stealth_gap.png', dpi=300)
    plt.close()

def generate_study1_deception_rates():
    df = pd.read_csv('logs/v2_study1/study1_results.csv')
    oversight_order = ['low', 'mid', 'high']
    gb_deception = df.groupby('oversight')['glassbox_category'].apply(lambda x: (x == 'COMPLIANT_DECEPTION').mean() * 100).reindex(oversight_order)
    bb_deception = df.groupby('oversight')['blackbox_category'].apply(lambda x: (x != 'ACCURATE').mean() * 100).reindex(oversight_order)
    
    plt.figure(figsize=(10, 6))
    plt.plot(gb_deception.index, gb_deception.values, marker='s', linewidth=3, markersize=10, color='#2c3e50', label='Glassbox')
    plt.plot(bb_deception.index, bb_deception.values, marker='o', linewidth=3, markersize=10, color='#e74c3c', label='Blackbox')
    plt.fill_between(oversight_order, bb_deception.values, gb_deception.values, color='gray', alpha=0.2, label='Stealth Gap')
    
    plt.xlabel('Oversight Level (Audit Rate)', fontsize=13)
    plt.ylabel('Deception Rate (%)', fontsize=13)
    plt.ylim(0, 100)
    plt.legend(fontsize=11, loc='upper left')
    
    for i, level in enumerate(oversight_order):
        gap = gb_deception[level] - bb_deception[level]
        plt.text(i, (gb_deception[level] + bb_deception[level])/2, f'Gap: {gap:.1f}%', 
                 ha='center', va='center', fontweight='bold', color='#2980b9', 
                 bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.2'))
                 
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('docs/final/images/study1_deception_rates.png', dpi=300)
    plt.close()

def generate_study1_deception_rates_grouped():
    df = pd.read_csv('logs/v2_study1/study1_results.csv')
    def calc_rates(group):
        total = len(group)
        gb_deception = sum(group['glassbox_category'] == 'COMPLIANT_DECEPTION')
        bb_deception = sum(group['blackbox_category'].isin(['DECEPTIVE_FRAMING', 'OMITTED_CRITICAL', 'FABRICATED']))
        return pd.Series({
            'Glassbox': (gb_deception / total) * 100 if total > 0 else 0,
            'Blackbox': (bb_deception / total) * 100 if total > 0 else 0
        })
    rates = df.groupby('oversight').apply(calc_rates).reindex(['low', 'mid', 'high'])
    
    fig, ax = plt.subplots(figsize=(8, 6))
    x = np.arange(len(rates.index))
    width = 0.35
    
    rects1 = ax.bar(x - width/2, rates['Glassbox'], width, label='Glassbox', color='#2c3e50', edgecolor='white', zorder=3)
    rects2 = ax.bar(x + width/2, rates['Blackbox'], width, label='Blackbox', color='#e74c3c', edgecolor='white', zorder=3)
    
    ax.set_ylabel('Deception Rate (%)', fontsize=12)
    ax.set_xlabel('Oversight Level', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(['Low', 'Medium', 'High'], fontsize=11)
    ax.set_ylim(0, 105)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7, zorder=0)
    ax.legend(fontsize=11)
    
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.1f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 5), textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, fontweight='bold')
    autolabel(rects1)
    autolabel(rects2)
    
    plt.tight_layout()
    plt.savefig('docs/final/images/study1_deception_rates_grouped.png', dpi=300, bbox_inches='tight')
    plt.close()

def generate_study2_framing_bars():
    df = pd.read_csv('logs/v2_study2/study2_results.csv')
    
    # Extract framing from run_id
    df['framing'] = df['run_id'].apply(lambda x: x.split('/')[2])
    
    framing_order = ['bare', 'self_serving', 'moral']
    framing_labels = ['Bare', 'Self-Serving', 'Moral']
    
    def calc_rates(group):
        total = len(group)
        gb_deception = sum(group['glassbox_category'] == 'COMPLIANT_DECEPTION')
        bb_deception = sum(group['blackbox_category'].isin(['DECEPTIVE_FRAMING', 'OMITTED_CRITICAL', 'FABRICATED']))
        return pd.Series({
            'Glassbox': (gb_deception / total) * 100 if total > 0 else 0,
            'Blackbox': (bb_deception / total) * 100 if total > 0 else 0
        })
        
    rates = df.groupby('framing').apply(calc_rates).reindex(framing_order)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    x = np.arange(len(rates.index))
    width = 0.35
    
    # Colors consistent with Study 1 Grouped Chart
    rects1 = ax.bar(x - width/2, rates['Glassbox'], width, label='Glassbox', color='#2c3e50', edgecolor='white', zorder=3)
    rects2 = ax.bar(x + width/2, rates['Blackbox'], width, label='Blackbox', color='#e74c3c', edgecolor='white', zorder=3)
    
    # Add horizontal trend lines for both
    gb_mean = rates['Glassbox'].mean()
    bb_mean = rates['Blackbox'].mean()
    
    ax.axhline(gb_mean, color='#2c3e50', linestyle='--', linewidth=1.5, alpha=0.5, zorder=2)
    ax.axhline(bb_mean, color='#e74c3c', linestyle='--', linewidth=1.5, alpha=0.5, zorder=2)
    
    ax.set_ylabel('Deception Rate (%)', fontsize=12)
    ax.set_xlabel('Hidden Goal Framing', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(framing_labels, fontsize=11)
    ax.set_ylim(0, 105)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7, zorder=0)
    ax.legend(fontsize=11, loc='lower right')
    
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.1f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 5), textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, fontweight='bold')
                        
    autolabel(rects1)
    autolabel(rects2)
    
    plt.tight_layout()
    plt.savefig('docs/final/images/study2_framing_bars.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    setup_theme()
    print("Generating v1 and v2 composition charts dynamically...")
    generate_composition_charts()
    print("Generating v1_frontier_stealth_gap.png...")
    generate_v1_frontier_stealth_gap()
    print("Generating study1_deception_rates.png...")
    generate_study1_deception_rates()
    print("Generating study1_deception_rates_grouped.png...")
    generate_study1_deception_rates_grouped()
    print("Generating study2_framing_bars.png...")
    generate_study2_framing_bars()
    print("All final visualizations generated successfully directly into docs/final/images/.")
