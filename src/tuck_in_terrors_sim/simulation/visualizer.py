# src/tuck_in_terrors_sim/simulation/visualizer.py
import os
from typing import List, Dict, Any
from collections import Counter
import matplotlib.pyplot as plt

class Visualizer:
    """Creates and saves visualizations of simulation results."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Configure plot style
        plt.style.use('seaborn-v0_8-darkgrid')
        self.fig_size = (10, 6)
        self.title_font_size = 16
        self.label_font_size = 12

    def plot_win_loss_pie(self, results: List[Dict[str, Any]], ai_profile: str):
        """Generates a pie chart of win/loss outcomes."""
        if not results: return

        statuses = [r['win_status'] for r in results]
        counts = Counter(statuses)
        
        labels = list(counts.keys())
        sizes = list(counts.values())
        
        fig, ax = plt.subplots(figsize=self.fig_size)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, textprops={'fontsize': self.label_font_size})
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        
        title = f'Win/Loss Outcome Distribution ({ai_profile})'
        plt.title(title, fontsize=self.title_font_size)
        
        file_path = os.path.join(self.output_dir, f'outcomes_pie_{ai_profile}.png')
        plt.savefig(file_path)
        plt.close(fig)
        print(f"Saved pie chart to {file_path}")

    def plot_turn_distribution_hist(self, results: List[Dict[str, Any]], ai_profile: str):
        """Generates a histogram of the final turn number for wins and losses."""
        if not results: return

        win_turns = [r['final_turn'] for r in results if 'WIN' in r['win_status']]
        loss_turns = [r['final_turn'] for r in results if 'LOSS' in r['win_status']]

        fig, ax = plt.subplots(figsize=self.fig_size)
        
        # Plot histograms
        ax.hist(win_turns, bins=range(1, max(win_turns + loss_turns) + 2), alpha=0.7, label='Wins', color='green', rwidth=0.85)
        ax.hist(loss_turns, bins=range(1, max(win_turns + loss_turns) + 2), alpha=0.7, label='Losses', color='red', rwidth=0.85)
        
        ax.set_xlabel('Final Turn Number', fontsize=self.label_font_size)
        ax.set_ylabel('Number of Games', fontsize=self.label_font_size)
        title = f'Game Length Distribution ({ai_profile})'
        ax.set_title(title, fontsize=self.title_font_size)
        ax.legend()
        ax.set_xticks(range(1, max(win_turns + loss_turns) + 1))

        file_path = os.path.join(self.output_dir, f'turn_dist_hist_{ai_profile}.png')
        plt.savefig(file_path)
        plt.close(fig)
        print(f"Saved histogram to {file_path}")