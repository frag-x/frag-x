function love.load()

  love.mouse.setRelativeMode(true)

  Object = require "classic"
  require "player"

  love.physics.setMeter(64) --the height of a meter our worlds will be 64px
  world = love.physics.newWorld(0, 0, true) --create a world for the bodies to exist in with horizontal gravity of 0 and vertical gravity of 9.81

  width = 650
  height = 650


   objects = {} -- table to hold all our physical objects


   setup_map(objects)
   
 
   player = Player(world, width, height, 20, 200)

  --let's create a couple blocks to play around with
  objects.block1 = {}
  objects.block1.body = love.physics.newBody(world, 200, 550, "dynamic")
  objects.block1.shape = love.physics.newRectangleShape(0, 0, 50, 100)
  objects.block1.fixture = love.physics.newFixture(objects.block1.body, objects.block1.shape, 5) -- A higher density gives it more mass.

  objects.block2 = {}
  objects.block2.body = love.physics.newBody(world, 200, 400, "dynamic")
  objects.block2.shape = love.physics.newRectangleShape(0, 0, 100, 50)
  objects.block2.fixture = love.physics.newFixture(objects.block2.body, objects.block2.shape, 2)


  --initial graphics setup
  love.graphics.setBackgroundColor(0.41, 0.53, 0.97) --set the background color to a nice blue
  love.window.setMode(width, height) --set the window dimensions to 650 by 650 with no fullscreen, vsync on, and no antialiasing
end

function setup_map(objects)
   barrierThickness = 50
  
  objects.bottom = {}
  objects.bottom.body = love.physics.newBody(world, width/2, height-(barrierThickness/2))
  objects.bottom.shape = love.physics.newRectangleShape(width, barrierThickness)
  objects.bottom.fixture = love.physics.newFixture(objects.bottom.body, objects.bottom.shape)

  objects.top = {}
  objects.top.body = love.physics.newBody(world, width/2, (barrierThickness/2))
  objects.top.shape = love.physics.newRectangleShape(width, barrierThickness)
  objects.top.fixture = love.physics.newFixture(objects.top.body, objects.top.shape)

  objects.right = {}
  objects.right.body = love.physics.newBody(world, width-(barrierThickness/2), height/2)
  objects.right.shape = love.physics.newRectangleShape(barrierThickness, height)
  objects.right.fixture = love.physics.newFixture(objects.right.body, objects.right.shape)

  objects.left = {}
  objects.left.body = love.physics.newBody(world, (barrierThickness/2), height/2)
  objects.left.shape = love.physics.newRectangleShape(barrierThickness, height)
  objects.left.fixture = love.physics.newFixture(objects.left.body, objects.left.shape)

end

function love.update(dt)
  world:update(dt) --this puts the world into motion
  player:update(dt) -- this allows player to produce motion
  print(player:inputStateAsText())
end


function love.mousemoved(X,Y,DX,DY)
  x,y,dx,dy = X,Y,DX,DY
  player.rotationAngle = player.rotationAngle + dx * player.sensitivity
  -- player.rotationAngle = (player.rotationAngle + dx * player.sensitivity) % (math.pi * 2)
end

function bool_to_number(value)
  return value and 1 or 0
end


function love.draw()
  love.graphics.setColor(0.28, 0.63, 0.05) 
  -- Draw walls
  love.graphics.polygon("fill", objects.bottom.body:getWorldPoints(objects.bottom.shape:getPoints())) 
  love.graphics.polygon("fill", objects.top.body:getWorldPoints(objects.top.shape:getPoints())) 
  love.graphics.polygon("fill", objects.left.body:getWorldPoints(objects.left.shape:getPoints())) 
  love.graphics.polygon("fill", objects.right.body:getWorldPoints(objects.right.shape:getPoints())) 

  love.graphics.setColor(0.76, 0.18, 0.05) 
  love.graphics.circle("fill", player.body:getX(), player.body:getY(), player.shape:getRadius())

  -- Draw aim line
  love.graphics.line(player.body:getX(), player.body:getY(), player.body:getX() + math.cos(player.rotationAngle) * player.aimLength , player.body:getY()+ math.sin(player.rotationAngle) * player.aimLength)

  love.graphics.setColor(0.20, 0.20, 0.20) 
  love.graphics.polygon("fill", objects.block1.body:getWorldPoints(objects.block1.shape:getPoints()))
  love.graphics.polygon("fill", objects.block2.body:getWorldPoints(objects.block2.shape:getPoints()))
end

