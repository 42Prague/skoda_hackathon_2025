import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Brain, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { authAPI } from "@/lib/api";

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { toast } = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [demoEmployee, setDemoEmployee] = useState<{email: string; employeeId: string; firstName: string; lastName: string} | null>(null);
  const [demoManager, setDemoManager] = useState<{email: string; employeeId: string} | null>(null);

  // Fetch demo employees from API (real employees from database)
  useEffect(() => {
    const fetchDemoEmployees = async () => {
      try {
        const data = await authAPI.getDemoEmployees();
        if (data.employee) {
          setDemoEmployee(data.employee);
        }
        if (data.manager) {
          setDemoManager(data.manager);
        }
      } catch (error) {
        console.error('Failed to fetch demo employees:', error);
        // If API fails, use fallback (will fail if employee doesn't exist)
      }
    };

    fetchDemoEmployees();
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await login(email, password);
      toast({
        title: "Login Successful",
        description: "Welcome back!",
      });
      navigate("/employee-new");
    } catch (error: any) {
      toast({
        title: "Login Failed",
        description: error.message || "Invalid email or password",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async (role: 'manager' | 'employee') => {
    setIsLoading(true);
    
    // Use real employees from the database (fetched from API)
    let credentials;
    
    if (role === 'manager') {
      // Use manager from database or fallback
      credentials = demoManager 
        ? { email: demoManager.email, password: 'password123' }
        : { email: 'karel.vagner@skoda.cz', password: 'password123' };
    } else {
      // Use first employee from database or fallback
      credentials = demoEmployee
        ? { email: demoEmployee.email, password: 'password123' }
        : { email: 'lenka.prochazka.4241@skoda.cz', password: 'password123' };
    }

    try {
      await login(credentials.email, credentials.password);
      toast({
        title: "Demo Login Successful",
        description: `Logged in as ${role === 'manager' ? 'Manager' : 'Employee'}`,
      });
      navigate(role === 'manager' ? '/manager-new' : '/employee-new');
    } catch (error: any) {
      toast({
        title: "Demo Login Failed",
        description: error.message || "Demo account not found. Run 'npm run db:seed:real' in backend.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-subtle flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-12 h-12 rounded-lg bg-gradient-primary flex items-center justify-center">
              <Brain className="w-8 h-8 text-primary-foreground" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-foreground">AI Skill Coach</h1>
          <p className="text-muted-foreground">Sign in to access your personalized dashboard</p>
        </div>

        {/* Login Card */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Login</CardTitle>
            <CardDescription>Enter your credentials to continue</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="firstname.lastname@skoda.cz"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
              <Button 
                type="submit" 
                className="w-full bg-gradient-primary" 
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  'Sign In'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Demo Login Card */}
        <Card className="shadow-lg border-primary/20">
          <CardHeader>
            <CardTitle className="text-sm">Quick Demo Access</CardTitle>
            <CardDescription className="text-xs">
              Login with real data from your dataset
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              variant="outline"
              className="w-full"
              onClick={() => handleDemoLogin('employee')}
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                '👤 Employee Dashboard'
              )}
            </Button>
            <Button
              variant="outline"
              className="w-full"
              onClick={() => handleDemoLogin('manager')}
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                '👔 Manager Dashboard'
              )}
            </Button>
            <div className="text-xs text-muted-foreground text-center pt-2">
              {demoManager && (
                <p>Manager: {demoManager.email}</p>
              )}
              {demoEmployee ? (
                <>
                  <p>Employee ID: <strong>{demoEmployee.employeeId}</strong> (Real from dataset)</p>
                  <p>Email: {demoEmployee.email}</p>
                  <p>Name: {demoEmployee.firstName} {demoEmployee.lastName}</p>
                </>
              ) : (
                <>
                  <p>Employee ID: <strong>00004241</strong> (Real from dataset)</p>
                  <p>Loading employee...</p>
                </>
              )}
              <p>Password: password123</p>
            </div>
          </CardContent>
        </Card>

        {/* Info Card */}
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="pt-6">
            <div className="text-xs text-muted-foreground space-y-2">
              <p>✅ <strong>Real Data Connected:</strong> Using data from your CSV files</p>
              <p>📊 <strong>Employees</strong> from ERP_SK1.Start_month - SE.csv</p>
              <p>🎯 <strong>Skills</strong> from Skill_mapping.csv</p>
              <p>📚 <strong>Courses</strong> from ZHRPD_VZD_STA_007.csv</p>
              {demoEmployee ? (
                <>
                  <p>👤 <strong>Demo Employee ID:</strong> <strong className="text-primary">{demoEmployee.employeeId}</strong> (Real ID from dataset)</p>
                  <p>📧 <strong>Email:</strong> {demoEmployee.email}</p>
                  <p>👤 <strong>Name:</strong> {demoEmployee.firstName} {demoEmployee.lastName}</p>
                </>
              ) : (
                <p>👤 <strong>Demo Employee ID:</strong> <strong className="text-primary">Loading...</strong></p>
              )}
              <p className="text-primary mt-2 font-semibold">💡 All data shown is from the dataset for this employee ID!</p>
            </div>
          </CardContent>
        </Card>

        <div className="text-center">
          <Button
            variant="link"
            onClick={() => navigate("/")}
            className="text-muted-foreground"
          >
            ← Back to Home
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Login;
