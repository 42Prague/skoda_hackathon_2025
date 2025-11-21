import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useNavigate } from "react-router-dom";
import { 
  Users, 
  UserCircle, 
  TrendingUp, 
  Brain, 
  ChevronRight, 
  Sparkles,
  Target,
  Zap,
  Layers,
  ArrowRight,
  Play,
  Award,
  BookOpen,
  Lightbulb
} from "lucide-react";
import { motion, useScroll, useTransform, useSpring, useInView } from "framer-motion";
import { useInView as useIntersectionObserver } from "react-intersection-observer";
import { useRef, useEffect, useState } from "react";
import heroIllustration from "@/assets/hero-illustration.png";

const Index = () => {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: containerRef });
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  // Scroll to Choose Your Path section
  const scrollToChoosePath = () => {
    const element = document.getElementById('choose-your-path');
    if (element) {
      const yOffset = -80; // Offset for fixed header
      const y = element.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  };

  // Smooth scrollY progress
  const smoothProgress = useSpring(scrollYProgress, { stiffness: 100, damping: 30 });

  // Parallax transforms
  const heroY = useTransform(smoothProgress, [0, 1], ["0%", "50%"]);
  const heroOpacity = useTransform(smoothProgress, [0, 0.3], [1, 0]);
  const bgY = useTransform(smoothProgress, [0, 1], ["0%", "30%"]);

  // Mouse tracking for interactive elements
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth - 0.5) * 20,
        y: (e.clientY / window.innerHeight - 0.5) * 20,
      });
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  // Animation variants
  const fadeInUp = {
    hidden: { opacity: 0, y: 60 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.8 }
    }
  };

  const staggerChildren = {
    visible: {
      transition: {
        staggerChildren: 0.2
      }
    }
  };

  return (
    <div ref={containerRef} className="relative overflow-x-hidden">
      {/* Animated Background */}
      <motion.div 
        style={{ y: bgY }}
        className="fixed inset-0 z-0"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-green-50 via-white to-blue-50" />
        <div className="absolute inset-0 opacity-30">
          {[...Array(20)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 bg-primary/20 rounded-full"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
              }}
              animate={{
                y: [0, -20, 0],
                opacity: [0.3, 0.8, 0.3],
              }}
              transition={{
                duration: 3 + Math.random() * 2,
                repeat: Infinity,
                delay: Math.random() * 2,
              }}
            />
          ))}
        </div>
      </motion.div>

      {/* Header */}
      <motion.header 
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="relative z-50 border-b bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60 sticky top-0"
      >
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <motion.div 
            className="flex items-center gap-3"
            whileHover={{ scale: 1.05 }}
            transition={{ duration: 0.2 }}
          >
            <motion.div 
              className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center relative overflow-hidden"
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.6 }}
            >
              <Brain className="w-7 h-7 text-primary-foreground relative z-10" />
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                animate={{ x: [-100, 100] }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              />
            </motion.div>
            <div>
              <h1 className="text-xl font-bold text-foreground">SkillBridge AI</h1>
              <p className="text-xs text-muted-foreground font-medium tracking-wide">ŠKODA Career Intelligence</p>
            </div>
          </motion.div>

          <motion.div 
            className="hidden md:flex items-center gap-6"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <Button 
              variant="ghost" 
              className="text-muted-foreground hover:text-foreground"
              onClick={scrollToChoosePath}
            >
              Features
            </Button>
            <Button 
              variant="ghost" 
              className="text-muted-foreground hover:text-foreground"
              onClick={() => navigate("/about")}
            >
              About
            </Button>
            <Button 
              className="bg-gradient-primary hover:opacity-90 shadow-lg"
              onClick={() => navigate("/login")}
            >
              Get Started
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </motion.div>
        </div>
      </motion.header>

      {/* Hero Section */}
      <section className="relative z-10 min-h-screen flex items-center">
        <motion.div
          style={{ y: heroY, opacity: heroOpacity }}
          className="container mx-auto px-4"
        >
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div 
              className="space-y-8"
              initial="hidden"
              animate="visible"
              variants={staggerChildren}
            >
              <motion.div 
                variants={fadeInUp}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium backdrop-blur-sm"
              >
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                >
                  <Sparkles className="w-4 h-4" />
                </motion.div>
                Powered by Advanced AI
              </motion.div>

              <motion.div variants={fadeInUp} className="space-y-4">
                <h1 className="text-5xl lg:text-7xl font-bold text-foreground leading-tight">
                  <span className="block">SkillBridge</span>
                  <span className="block bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                    Intelligence
                  </span>
                </h1>
                <h2 className="text-2xl lg:text-3xl text-secondary font-semibold">
                  Next-Generation Career Copilot
                </h2>
              </motion.div>

              <motion.p 
                variants={fadeInUp}
                className="text-xl text-muted-foreground max-w-xl leading-relaxed"
              >
                Transform your career journey with AI-powered insights. Navigate skill development, 
                discover opportunities, and accelerate growth with precision intelligence.
              </motion.p>

              <motion.div 
                variants={fadeInUp}
                className="flex flex-col sm:flex-row gap-4"
              >
                <Button 
                  size="lg" 
                  className="bg-gradient-primary hover:opacity-90 shadow-xl text-lg px-8 py-6 rounded-full group"
                  onClick={() => navigate("/login")}
                >
                  Start Your Journey
                  <motion.div
                    className="ml-2"
                    whileHover={{ x: 5 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ArrowRight className="w-5 h-5" />
                  </motion.div>
                </Button>
                <Button 
                  variant="outline" 
                  size="lg" 
                  className="text-lg px-8 py-6 rounded-full border-2 hover:bg-primary/5"
                >
                  <Play className="w-5 h-5 mr-2" />
                  Watch Demo
                </Button>
              </motion.div>
            </motion.div>

            <motion.div 
              className="relative lg:ml-12"
              initial={{ opacity: 0, scale: 0.8, rotateY: 20 }}
              animate={{ opacity: 1, scale: 1, rotateY: 0 }}
              transition={{ duration: 1, ease: "easeOut", delay: 0.3 }}
              style={{
                transform: `translate3d(${mousePosition.x * 0.5}px, ${mousePosition.y * 0.5}px, 0)`,
              }}
            >
              {/* Floating elements around the main illustration */}
              <motion.div
                className="absolute -top-4 -left-4 w-20 h-20 bg-gradient-primary rounded-2xl flex items-center justify-center shadow-lg"
                animate={{ 
                  y: [0, -10, 0],
                  rotate: [0, 5, 0] 
                }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              >
                <Target className="w-8 h-8 text-white" />
              </motion.div>

              <motion.div
                className="absolute -bottom-6 -right-6 w-16 h-16 bg-gradient-secondary rounded-full flex items-center justify-center shadow-lg"
                animate={{ 
                  y: [0, 10, 0],
                  scale: [1, 1.1, 1] 
                }}
                transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
              >
                <Lightbulb className="w-6 h-6 text-white" />
              </motion.div>

              <motion.div
                className="absolute top-1/4 -right-8 w-12 h-12 bg-gradient-to-r from-primary to-secondary rounded-lg flex items-center justify-center shadow-lg"
                animate={{ 
                  x: [0, 15, 0],
                  rotate: [0, 10, 0] 
                }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 1 }}
              >
                <Award className="w-5 h-5 text-white" />
              </motion.div>

              <div className="relative group">
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-primary/30 to-secondary/30 rounded-3xl blur-xl"
                  animate={{ 
                    scale: [1, 1.05, 1],
                    opacity: [0.5, 0.8, 0.5] 
                  }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                />
                <img 
                  src={heroIllustration} 
                  alt="Career Intelligence Platform" 
                  className="relative w-full h-auto rounded-3xl shadow-2xl group-hover:scale-105 transition-transform duration-500"
                />
              </div>
            </motion.div>
          </div>
        </motion.div>
      </section>

      {/* Dynamic Navigation Cards */}
      <DynamicNavigationSection navigate={navigate} />

      {/* Features Section */}
      <DynamicFeaturesSection />

      {/* Stats Section */}
      <DynamicStatsSection />

      {/* CTA Section */}
      <DynamicCTASection navigate={navigate} />
    </div>
  );
};

// Dynamic Navigation Section Component
const DynamicNavigationSection = ({ navigate }: { navigate: any }) => {
  const { ref, inView } = useIntersectionObserver({
    threshold: 0.2,
    triggerOnce: true,
  });

  return (
    <section ref={ref} className="relative z-10 py-24 bg-gradient-to-b from-white to-gray-50">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h3 id="choose-your-path" className="text-4xl font-bold text-foreground mb-4">Choose Your Path</h3>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Tailored experiences for every role in your organization
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={inView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.8, delay: 0.2 }}
            whileHover={{ scale: 1.05 }}
          >
            <Card 
              className="group p-8 hover:shadow-2xl transition-all cursor-pointer border-2 hover:border-primary bg-card relative overflow-hidden"
              onClick={() => navigate("/employee")}
            >
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent"
                initial={{ x: "-100%" }}
                whileHover={{ x: "100%" }}
                transition={{ duration: 0.8 }}
              />
              
              <div className="relative z-10 flex flex-col items-center text-center space-y-6">
                <motion.div 
                  className="w-24 h-24 rounded-3xl bg-gradient-primary flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg"
                  whileHover={{ rotate: 360 }}
                  transition={{ duration: 0.8 }}
                >
                  <UserCircle className="w-12 h-12 text-primary-foreground" />
                </motion.div>
                <div>
                  <h3 className="text-2xl font-bold text-foreground mb-2">Employee Hub</h3>
                  <p className="text-muted-foreground">
                    Discover personalized career paths, skill recommendations, and learning opportunities
                  </p>
                </div>
                <Button className="mt-4 bg-gradient-primary hover:opacity-90 group-hover:scale-105 transition-transform">
                  Enter Dashboard
                  <ChevronRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </Button>
              </div>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={inView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.8, delay: 0.4 }}
            whileHover={{ scale: 1.05 }}
          >
            <Card 
              className="group p-8 hover:shadow-2xl transition-all cursor-pointer border-2 hover:border-secondary bg-card relative overflow-hidden"
              onClick={() => navigate("/manager")}
            >
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-secondary/5 to-transparent"
                initial={{ x: "-100%" }}
                whileHover={{ x: "100%" }}
                transition={{ duration: 0.8 }}
              />
              
              <div className="relative z-10 flex flex-col items-center text-center space-y-6">
                <motion.div 
                  className="w-24 h-24 rounded-3xl bg-gradient-secondary flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg"
                  whileHover={{ rotate: 360 }}
                  transition={{ duration: 0.8 }}
                >
                  <Users className="w-12 h-12 text-secondary-foreground" />
                </motion.div>
                <div>
                  <h3 className="text-2xl font-bold text-foreground mb-2">Manager Central</h3>
                  <p className="text-muted-foreground">
                    Team analytics, skill gap analysis, and strategic workforce planning
                  </p>
                </div>
                <Button variant="secondary" className="mt-4 group-hover:scale-105 transition-transform">
                  Enter Dashboard
                  <ChevronRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </Button>
              </div>
            </Card>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

// Dynamic Features Section Component
const DynamicFeaturesSection = () => {
  const { ref, inView } = useIntersectionObserver({
    threshold: 0.1,
    triggerOnce: true,
  });

  const features = [
    {
      icon: Brain,
      title: "AI-Powered Insights",
      description: "Advanced machine learning algorithms analyze market trends and skill demands",
      gradient: "from-blue-500 to-purple-600"
    },
    {
      icon: Target,
      title: "Precision Matching",
      description: "Smart recommendations based on your unique profile and career aspirations",
      gradient: "from-green-500 to-teal-600"
    },
    {
      icon: TrendingUp,
      title: "Growth Analytics",
      description: "Real-time tracking of skill development and career progression",
      gradient: "from-orange-500 to-red-600"
    },
    {
      icon: Layers,
      title: "Skill Mapping",
      description: "Comprehensive visualization of your competency landscape",
      gradient: "from-indigo-500 to-blue-600"
    },
    {
      icon: Zap,
      title: "Instant Feedback",
      description: "Immediate insights and recommendations as you learn and grow",
      gradient: "from-yellow-500 to-orange-600"
    },
    {
      icon: Users,
      title: "Team Synergy",
      description: "Collaborative tools for managers and employees to align goals",
      gradient: "from-pink-500 to-purple-600"
    }
  ];

  return (
    <section ref={ref} className="relative z-10 py-24 bg-gradient-to-b from-gray-50 to-white">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h3 className="text-4xl font-bold text-foreground mb-4">Intelligent Career Acceleration</h3>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Leverage cutting-edge technology to transform your career development experience
          </p>
        </motion.div>

        <motion.div 
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-8"
          initial="hidden"
          animate={inView ? "visible" : "hidden"}
          variants={{
            visible: {
              transition: {
                staggerChildren: 0.1
              }
            }
          }}
        >
          {features.map((feature, index) => (
            <motion.div
              key={index}
              variants={{
                hidden: { opacity: 0, y: 50 },
                visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
              }}
              whileHover={{ y: -10, transition: { duration: 0.3 } }}
              className="group"
            >
              <Card className="p-8 h-full hover:shadow-lg transition-all bg-card border-2 hover:border-primary/20 relative overflow-hidden">
                <motion.div
                  className={`absolute inset-0 bg-gradient-to-r ${feature.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-500`}
                />
                
                <div className="relative z-10 space-y-4">
                  <motion.div 
                    className={`w-16 h-16 rounded-2xl bg-gradient-to-r ${feature.gradient} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}
                    whileHover={{ rotate: 360 }}
                    transition={{ duration: 0.6 }}
                  >
                    <feature.icon className="w-8 h-8 text-white" />
                  </motion.div>
                  <h4 className="text-xl font-bold text-foreground group-hover:text-primary transition-colors">
                    {feature.title}
                  </h4>
                  <p className="text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

// Dynamic Stats Section Component
const DynamicStatsSection = () => {
  const { ref, inView } = useIntersectionObserver({
    threshold: 0.5,
    triggerOnce: true,
  });

  const stats = [
    { value: 95, suffix: "%", label: "Accuracy Rate" },
    { value: 1200, suffix: "+", label: "Active Users" },
    { value: 87, suffix: "%", label: "Skill Match Success" },
    { value: 450, suffix: "+", label: "Career Transitions" }
  ];

  return (
    <section ref={ref} className="relative z-10 py-24 bg-gradient-to-r from-primary to-secondary">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={inView ? { opacity: 1, scale: 1 } : {}}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h3 className="text-4xl font-bold text-white mb-4">Proven Results</h3>
          <p className="text-xl text-white/90 max-w-2xl mx-auto">
            Numbers that speak to our commitment to career excellence
          </p>
        </motion.div>

        <div className="grid md:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 50 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="text-center group"
            >
              <motion.div 
                className="text-5xl font-bold text-white mb-2 group-hover:scale-110 transition-transform"
                initial={{ scale: 0 }}
                animate={inView ? { scale: 1 } : {}}
                transition={{ duration: 0.8, delay: index * 0.1 + 0.3, type: "spring", bounce: 0.4 }}
              >
                <CountUpNumber value={stat.value} suffix={stat.suffix} inView={inView} delay={index * 0.1} />
              </motion.div>
              <p className="text-white/90 text-lg font-medium">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Count Up Animation Component
const CountUpNumber = ({ value, suffix, inView, delay }: { value: number; suffix: string; inView: boolean; delay: number }) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (inView) {
      const timer = setTimeout(() => {
        let current = 0;
        const increment = value / 50;
        const interval = setInterval(() => {
          current += increment;
          if (current >= value) {
            setCount(value);
            clearInterval(interval);
          } else {
            setCount(Math.floor(current));
          }
        }, 40);
        return () => clearInterval(interval);
      }, delay * 1000);
      return () => clearTimeout(timer);
    }
  }, [inView, value, delay]);

  return <span>{count}{suffix}</span>;
};

// Dynamic CTA Section Component
const DynamicCTASection = ({ navigate }: { navigate: any }) => {
  const { ref, inView } = useIntersectionObserver({
    threshold: 0.3,
    triggerOnce: true,
  });

  return (
    <section ref={ref} className="relative z-10 py-24 bg-gradient-to-b from-white to-gray-100">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
          className="text-center max-w-4xl mx-auto"
        >
          <h3 className="text-5xl font-bold text-foreground mb-6">
            Ready to Transform Your Career?
          </h3>
          <p className="text-xl text-muted-foreground mb-12 leading-relaxed">
            Join thousands of professionals who have accelerated their growth with SkillBridge AI. 
            Your intelligent career companion is just one click away.
          </p>

          <motion.div
            className="flex flex-col sm:flex-row gap-6 justify-center"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={inView ? { opacity: 1, scale: 1 } : {}}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <Button 
              size="lg" 
              className="bg-gradient-primary hover:opacity-90 shadow-xl text-lg px-12 py-6 rounded-full group"
              onClick={() => navigate("/employee")}
            >
              Start Free Today
              <motion.div
                className="ml-2"
                whileHover={{ x: 5 }}
                transition={{ duration: 0.2 }}
              >
                <Sparkles className="w-5 h-5" />
              </motion.div>
            </Button>
            
            <Button 
              variant="outline" 
              size="lg" 
              className="text-lg px-12 py-6 rounded-full border-2 hover:bg-primary/5"
            >
              <BookOpen className="w-5 h-5 mr-2" />
              Learn More
            </Button>
          </motion.div>

          <motion.p
            className="text-sm text-muted-foreground mt-8"
            initial={{ opacity: 0 }}
            animate={inView ? { opacity: 1 } : {}}
            transition={{ duration: 0.8, delay: 0.6 }}
          >
            No credit card required • Instant access • GDPR compliant
          </motion.p>
        </motion.div>
      </div>
    </section>
  );
};

export default Index;
