import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, TrendingUp, Trash2 } from 'lucide-react';
import { API_BASE } from '../config';

export default function WatchlistsNew() {
  const [watchlists, setWatchlists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newWatchlistName, setNewWatchlistName] = useState('');
  useEffect(() => {
    fetchWatchlists();
  }, []);

  const fetchWatchlists = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/watchlists`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setWatchlists(data);
      }
    } catch (error) {
      console.error('Error fetching watchlists:', error);
    } finally {
      setLoading(false);
    }
  };

  const createWatchlist = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE}/api/watchlists`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name: newWatchlistName }),
      });

      if (response.ok) {
        await fetchWatchlists();
        setNewWatchlistName('');
        setShowCreateModal(false);
      }
    } catch (error) {
      console.error('Error creating watchlist:', error);
    }
  };

  const deleteWatchlist = async (id, name) => {
    if (!confirm(`Delete "${name}"?`)) return;

    try {
      const response = await fetch(`${API_BASE}/api/watchlists/${id}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (response.ok) {
        await fetchWatchlists();
      }
    } catch (error) {
      console.error('Error deleting watchlist:', error);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Skeleton className="h-10 w-40 mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-4 w-24 mt-2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-20" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8">
        {/* Create Button */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-muted-foreground">
              {watchlists.length} {watchlists.length === 1 ? 'Watchlist' : 'Watchlists'}
            </h2>
          </div>
          <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Watchlist
              </Button>
            </DialogTrigger>
            <DialogContent>
              <form onSubmit={createWatchlist}>
                <DialogHeader>
                  <DialogTitle>Create Watchlist</DialogTitle>
                  <DialogDescription>
                    Create a new watchlist to organize your favorite stocks.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Watchlist Name</Label>
                    <Input
                      id="name"
                      placeholder="e.g., Tech Stocks"
                      value={newWatchlistName}
                      onChange={(e) => setNewWatchlistName(e.target.value)}
                      required
                      maxLength={50}
                      autoFocus
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowCreateModal(false);
                      setNewWatchlistName('');
                    }}
                  >
                    Cancel
                  </Button>
                  <Button type="submit">Create</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Watchlists Grid */}
        {watchlists.length === 0 ? (
          <Card className="col-span-full">
            <CardContent className="flex flex-col items-center justify-center py-16">
              <TrendingUp className="h-12 w-12 text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-semibold mb-2">No watchlists yet</h3>
              <p className="text-muted-foreground mb-6 text-center">
                Create your first watchlist to start tracking stocks
              </p>
              <Button onClick={() => setShowCreateModal(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create Watchlist
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {watchlists.map((watchlist) => (
              <Card
                key={watchlist.id}
                className="group hover:shadow-lg transition-shadow cursor-pointer"
              >
                <Link to={`/watchlists/${watchlist.id}`}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="group-hover:text-primary transition-colors">
                          {watchlist.name}
                        </CardTitle>
                        <CardDescription className="mt-1.5">
                          Created {new Date(watchlist.created_at).toLocaleDateString()}
                        </CardDescription>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="opacity-0 group-hover:opacity-100 transition-opacity -mt-2 -mr-2"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          deleteWatchlist(watchlist.id, watchlist.name);
                        }}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </CardHeader>
                  <Separator />
                  <CardFooter className="pt-4">
                    <div className="flex items-center gap-2">
                      <Badge variant={watchlist.items_count > 0 ? "default" : "secondary"}>
                        {watchlist.items_count} {watchlist.items_count === 1 ? 'stock' : 'stocks'}
                      </Badge>
                    </div>
                  </CardFooter>
                </Link>
              </Card>
            ))}
          </div>
        )}

        {/* Limit Warning */}
        {watchlists.length >= 10 && (
          <div className="mt-6 p-4 bg-muted rounded-lg border">
            <p className="text-sm text-muted-foreground text-center">
              Maximum watchlists reached (10/10)
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
