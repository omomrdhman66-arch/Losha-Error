STATS={'combos':0,'approved':0,'charged':0,'errors':0}

def inc(k,n=1): STATS[k]=STATS.get(k,0)+n

def snapshot(): return dict(STATS)
